# Batch 9 Findings — Research Agent

Files processed: 20
Date range: 2026-02-28 to 2026-03-03

---

## 2026-02-28-bingx-dashboard-v1-1-build.md
**Date:** 2026-02-28
**Type:** Build session

### What happened
Built the first interactive BingX live dashboard as a Dash 4.0 app. Three files created: `bingx-live-dashboard-v1-1.py` (~720 lines), `assets/dashboard.css` (~28 lines), and `scripts/test_dashboard.py` (~275 lines). The dashboard had 5 tabs (Operational, History, Analytics, Coin Summary, Bot Controls), 14 callbacks, AG Grid, dark theme, and BingX API integration. Interactive actions included Raise BE and Move SL via the BingX REST API.

During a logic audit, 3 bugs were found and fixed before delivery: (1) CRITICAL — CB-6/CB-7 sent USD notional as quantity to BingX API instead of contract quantity in coins; (2) MEDIUM — Raise BE callback placed stop at entry without checking mark price profit/loss direction; (3) MEDIUM — History tab only refreshed on filter change, not on data reload (State vs Input distinction). The TTP research log was also reviewed and noted that Approach C (BingX Native Trailing with activation gate) was already implemented in executor.py.

### Decisions recorded
- Used `importlib.util.spec_from_file_location` for hyphenated filename import in test scripts.
- All 3 bugs fixed before delivery.

### State changes
- 3 new files created: dashboard v1-1, CSS, test script.
- Bugs BUG1/BUG2/BUG3 identified and fixed in the same session.
- py_compile passed on both .py files.

### Open items recorded
- Future: could add Trail column to positions grid once TTP state fields are available.

### Notes
This is the first functional build of the BingX dashboard. Followed the user's corrected requirements (interactive management, not read-only). Prior Streamlit read-only build was discarded.

---

## 2026-02-28-bingx-dashboard-v1-2-build.md
**Date:** 2026-02-28
**Type:** Build session

### What happened
Designed and wrote a build script (`scripts/build_dashboard_v1_2.py`) for the v1-2 dashboard. The approach was surgical: read v1-1 (1645 lines), apply targeted `str.replace()` and line-based section replacements, then write v1-2 along with updated CSS and test script. 8 planned improvements were addressed covering: version bump, math import, chart axis labels, compute_metrics improvements, improved date pickers, clientside JS tab switching, Sharpe ratio annualization, and BE Hit Count / LSG% stubs returning "N/A" until the bot provides those columns.

Key technical choices: `suppress_callback_exceptions` kept True due to dynamic CB-5 action buttons; `.format()` used instead of f-strings in build script strings to avoid escaped quotes rule; date pickers default to None (show all trades).

### Decisions recorded
- Clientside JS callback replaces server-side CB-2 for instant tab switching.
- Sharpe ratio annualized with sqrt(365) from daily PnL groupby.
- BE Hit Count and LSG% return "N/A" until bot writes those columns to trades.csv.
- `.format()` used instead of f-strings in build scripts (escaped quotes rule).

### State changes
- Build script written: `scripts/build_dashboard_v1_2.py`, py_compile OK.
- NOT YET RUN by user at time of logging.

### Open items recorded
- User to run build script, then tests, then dashboard visual verification.

### Notes
None.

---

## 2026-02-28-bingx-dashboard-v1-3-patch.md
**Date:** 2026-02-28
**Type:** Build session (patch)

### What happened
User ran v1-2 build and tested the dashboard live. Reported 11 visual/calculation issues via screenshots. Issues triaged into P1-P10 patches plus one non-dashboard issue (LSG%/BE Hits N/A = expected, bot-side fix needed). A build script `scripts/build_dashboard_v1_3.py` was written applying 15 text replacements + 1 section replacement.

Patches covered: CSS tab class names fixed, comprehensive CSS expansion from ~95 to ~270 lines (AG Grid, DatePickerRange, Dropdown all covered), input field contrast improved, number spinner styling, analytics/grade comparison width constraints, max DD% bug fixed (guard for small peak equity, capped at -100%), pd.read_json deprecation fixed with StringIO wrapper, "Daily PnL" renamed to "Realized PnL", version bump.

### Decisions recorded
- Max DD% guard: skip when peak < $1.0, cap at -100%.
- StringIO wrapper required for pd.read_json in pandas 2.x.
- LSG% and BE Hits are an expected N/A until bot writes `be_raised` and `saw_green` columns.

### State changes
- Build script `scripts/build_dashboard_v1_3.py` written, py_compile OK.
- NOT YET RUN by user at time of logging.

### Open items recorded
- Future: bot-side fix to write `be_raised` + `saw_green` to trades.csv on trade close.

### Notes
None.

---

## 2026-02-28-bingx-dashboard-vince-planning.md
**Date:** 2026-02-28
**Type:** Planning session (two sessions appended)

### What happened
**Session 1:** Pure planning session — no code written. User stopped the build because layout was designed without asking. A plan was approved covering build order: BingX dashboard first, then Vince B1 through B6. Data was confirmed from live files: state.json schema (5 open positions, all BE raised), trades.csv columns, and live config.yaml (`demo_mode: false`, $5 margin, 10x leverage, 47 coins, no fixed TP).

**Session 2 (appended):** User started with explicit requirement "position management." Claude had added "read-only" to a prior plan note (Session 1 assumption), then built a Streamlit read-only version — wrong technology and wrong interactivity. User corrected: had never said "read-only." This session confirmed the read-only assumption came from Claude's own plan note, not from the user. The next session was directed to build an interactive Dash dashboard with Raise BE, Move SL, and per-row actions. A CLAUDE.md rule was agreed: "Management" = interactive. "Monitoring" = read-only. Ambiguous = ask.

### Decisions recorded
- Build order: BingX dashboard -> B1 -> B2 -> B3 -> B4 -> B5 -> B6.
- No background agents; sequential build; user runs verify after each block.
- Ollama (qwen3:8b) handles boilerplate-only files.
- Interactive Dash dashboard required with 3 tabs: Positions, History, Coin Summary.
- Positions tab actions: Raise to Breakeven, Move SL (calls BingX API).
- New CLAUDE.md rule: Management = interactive, Monitoring = read-only.

### State changes
- Plan files created (system + vault copy).
- Wrong Streamlit build (`bingx-live-dashboard-v1.py`) created and discarded.
- CLAUDE.md rule added regarding UI interactivity.

### Open items recorded
- Before building, ask user layout/UX questions. (Addressed in v1-1 session.)
- Before Vince B1: Read `signals/four_pillars.py` and `signals/state_machine.py`.

### Notes
This is the root cause session for the read-only vs interactive dispute. Log confirms user never used the word "read-only" anywhere — the assumption was entirely Claude's.

---

## 2026-02-28-bingx-trade-analysis-be-session.md
**Date:** 2026-02-28
**Type:** Build session + bug fix

### What happened
Three deliverables completed: (1) `scripts/analyze_trades.py` — a Phase 3 trade analysis script fetching live mark prices and BingX auth API open orders to compute 3-scenario True Total P&L. Constants: `COMMISSION_TAKER=0.0005`, `COMMISSION_RT_GROSS=0.001`, `COMMISSION_REBATE=0.50`, `BE_TOLERANCE=0.0005`, `MARGIN_USD=5.0`, `LEVERAGE=10`. (2) BE+Fees analysis fix — `identify_be_trades` renamed to `identify_sl_at_entry_trades` with relabeled sections because SL-at-entry exits are NOT true breakeven (each costs ~$0.025 net exit commission). 17 SL-at-entry exits in Phase 3 = -$0.425 avoidable commission loss. True BE requires SL at `entry * 1.001` for LONG. (3) Two bot files patched: `main.py` fallback commission rate changed 0.0016 → 0.001, and `position_monitor.py` BE logging improved to show commission covered in USD, Telegram renamed from "BREAKEVEN RAISED" to "BE+FEES RAISED".

### Decisions recorded
- SL-at-entry exits are NOT true breakeven — they still incur exit commission.
- True BE+fees formula: LONG: `entry * (1 + commission_rate)`, SHORT: `entry * (1 - commission_rate)`.
- BingX taker commission is 0.05% (0.0005) per side, RT = 0.001 gross.

### State changes
- `scripts/analyze_trades.py`: `identify_be_trades` → `identify_sl_at_entry_trades`, sections relabeled.
- `main.py`: fallback commission 0.0016 → 0.001.
- `position_monitor.py`: BE logging improved; Telegram renamed.
- py_compile: all 3 files OK.

### Open items recorded
None stated.

### Notes
Commission rate in this session uses 0.05% per side (BingX). Later sessions and MEMORY.md confirm 0.08% (0.0008) as the correct rate. This discrepancy is noted — the fallback in main.py was changed to 0.001 (0.05% RT) but the actual live rate fetched from BingX API may differ.

---

## 2026-02-28-bingx-ttp-research.md
**Date:** 2026-02-28
**Type:** Research + build session

### What happened
Full research and implementation session for Trailing Take Profit (TTP). Root cause identified: `tp_atr_mult: null` in config.yaml with no trailing TP replacement meant 0 TP_HIT in 46 live trades (all SL_HIT or EXIT_UNKNOWN). BE raise was working but only provides a floor, not profit locking.

Six TTP approaches evaluated (A through E): A = Restore fixed TP, B = BingX native trailing immediate, C = BingX native trailing with activation gate (CHOSEN), D = AVWAP 2σ + 10-candle counter (future), E = Periodic SL ratchet (complement to C).

Approach C implemented: `config.yaml` additions (`trailing_activation_atr_mult: 2.0`, `trailing_rate: 0.02`), new `_place_trailing_order()` method in `executor.py` placing TRAILING_STOP_MARKET at `entry ± atr×2` with 2% callback rate. Three new unit tests in `tests/test_executor.py`. py_compile: PASS on both files.

### Decisions recorded
- Approach C (BingX native trailing with activation gate) chosen for live implementation.
- Approach D (AVWAP 2σ + 10-candle) deferred to future phase.
- Approach E (SL ratchet) is a complement, not standalone.
- Guard: trailing only runs if `trailing_rate`, `trailing_activation_atr_mult`, and `signal.atr` all set.

### State changes
- `config.yaml`: Added `trailing_activation_atr_mult: 2.0`, `trailing_rate: 0.02`.
- `executor.py`: New `_place_trailing_order()` method, stores `trailing_order_id` + `trailing_activation_price` in state.
- `tests/test_executor.py`: 3 new tests added.
- py_compile: PASS.

### Open items recorded
- Future: add AVWAP 2σ trigger (Approach D) to position_monitor.py.
- Watch bot log for `Trailing order placed:` on next entry.

### Notes
The BingX native trailing (Approach C, `trailing_activation_atr_mult: 2.0`) was later DISABLED in the 2026-03-03 session (both set to null) because it conflicted with the TTP engine. The TTP Python engine became the sole trailing mechanism.

---

## 2026-02-28-dash-skill-v12-community-audit.md
**Date:** 2026-02-28
**Type:** Skill enrichment session

### What happened
Upgraded the Dash skill from v1.1 to v1.2 via community audit. WebFetch to `community.plotly.com` was blocked by user permission hook; WebSearch was used instead (not subject to same hook). Ran 10 parallel searches covering 7 topics: extendData + Candlestick, dcc.Interval blocking, relayoutData infinite loop, ag-grid styleConditions, WebSocket vs dcc.Interval, background callback overhead, candlestick rangebreaks cliff.

Key community findings: OHLC dict key format is exact and deviation causes silent failure; dcc.Interval longer than callback causes queue buildup; relayoutData on candlestick can loop infinitely (fix: `xaxis.autorange = False`); `Math` not available in ag-grid condition strings; WebSocket 3x faster than polling for < 500ms updates; background callbacks only worthwhile for tasks > 10 seconds.

Appended Part 4 (~280 lines, 7 sections) to `C:\Users\User\.claude\skills\dash\SKILL.md`, version bumped v1.1 → v1.2.

### Decisions recorded
- WebSearch = valid alternative to WebFetch when WebFetch is blocked by hook.
- Part 4 added: Community-Sourced Traps & Patterns.

### State changes
- `C:\Users\User\.claude\skills\dash\SKILL.md`: 1447 → 1730 lines, v1.1 → v1.2.

### Open items recorded
None.

### Notes
None.

---

## 2026-02-28-dashboard-v393-promote.md
**Date:** 2026-02-28
**Type:** Bug fix + promotion session

### What happened
Investigated P0.3 (dashboard v3.9.3 BLOCKED — IndentationError). Found the file already compiles clean — the backlog entry was stale, issue resolved in a prior session. Fixed a pre-existing silent date filter fallback bug in `apply_date_filter()`: when `len(df_filtered) < 100`, function silently returned the full unfiltered dataset. For 7d date range with stale parquet data, this meant showing the entire year with no warning. Fix: removed `< 100` silent fallback; added explicit warnings at 3 call sites and ValueError in sweep incremental path.

Dashboard runtime validated by user: loads, portfolio runs, 30d works, 7d now shows proper warning. v3.9.3 promoted to PRODUCTION.

### Decisions recorded
- v3.9.3 promoted to PRODUCTION.
- Silent date filter fallback removed — always return filtered data, show explicit warnings.

### State changes
- `scripts/dashboard_v393.py`: 5 edits (removed fallback, added 3 warnings, 1 ValueError, trailing newline).
- v3.9.3: py_compile PASS, runtime validated, PRODUCTION.
- v3.9.2: remains as stable fallback.

### Open items recorded
None.

### Notes
Log note said v3.9.3 had IndentationError (in backlog). Actual file compiled clean — stale backlog entry.

---

## 2026-02-28-parquet-data-catchup.md
**Date:** 2026-02-28
**Type:** Bug fix + build session

### What happened
Session to update the 1m candle parquet cache in the backtester (15 days stale since 2026-02-13). Data source confirmed: Bybit v5 API. Cache: 399 coins, 798 files (1m + 5m), 6.7 GB, spanning 2025-02-11 to 2026-02-13. Fetcher class: `BybitFetcher` in `data/fetcher.py`. The existing fetcher hardcodes 1m interval; 5m parquets came from a prior process. User decided 1m only for this session.

Bug found: `config.yaml` only lists 5 default coins; `--coins N` flag slices from that list so `--coins 399` still yields 5. No flag existed to discover symbols from cached parquets. Fix: added `--all` flag to `scripts/fetch_data.py` — when passed, discovers all symbols from existing `*_1m.parquet` files in cache dir. py_compile: PASS.

### Decisions recorded
- 1m data only for this session (5m deferred).
- `--all` flag added to discover symbols from existing parquets.

### State changes
- `scripts/fetch_data.py`: Added `--all` flag, moved `cache_dir` resolution above symbol determination.
- py_compile: PASS.
- Script updated, awaiting user execution.

### Open items recorded
- User to run: `python scripts/fetch_data.py --months 1 --all`.

### Notes
None.

---

## 2026-02-28-vince-b1-scope-audit.md
**Date:** 2026-02-28
**Type:** Research + spec writing (no code)

### What happened
User referenced `PROJECTS/four-pillars-backtester/BUILD-VINCE-B1-PLUGIN.md` — file did not exist. Session researched B1 scope from the approved build plan and plugin spec, then created the formal build spec. Sources read: approved B1-B10 plan, VINCE-PLUGIN-INTERFACE-SPEC-v1.md, VINCE-V2-CONCEPT-v2.md, base_v2.py ABC, existing four_pillars.py (conflict found), both backtester engine versions, position_v384.py, signals, run_backtest script.

Critical finding: `strategies/four_pillars.py` already existed with a v1 partial implementation. 6 issues in v1 file identified: wrong base class, missing 4/5 abstract methods, wrong signal import, wrong `compute_signals()` signature, separate enrichment method, legacy ML classifier methods. Engine decision: v385 over v384 (user confirmed) — v385 adds post-processing pass with LSG category and P&L path.

Output: `BUILD-VINCE-B1-PLUGIN.md` created with full spec including archive instruction, per-method guide, trade schema, imports, and 4 verification tests.

### Decisions recorded
- v385 engine over v384 (user confirmed).
- Existing `strategies/four_pillars.py` must be archived to `strategies/four_pillars_v1_archive.py` before B1 build.
- B1 uses `signals/four_pillars_v383_v2.py` (spec says; later found to be outdated — see 2026-03-03-session-handoff).
- `symbol` field not in Trade384 — must be injected by `run_backtest()` wrapper per symbol loop.

### State changes
- `BUILD-VINCE-B1-PLUGIN.md` created.
- `06-CLAUDE-LOGS/plans/2026-02-28-vince-b1-plugin-scope-audit.md` plan copy created.
- No code written.

### Open items recorded
- Confirm Q1/Q2 (mfe, mae, saw_green in Trade384) by reading position_v384.py.
- Complete B1 build (next step after this session).

### Notes
The signal import decision (v383_v2) was found to be outdated in the 2026-03-03-session-handoff log, which states B1 must use `signals/four_pillars_v386.py` instead.

---

## 2026-02-28-vince-b4-scope-audit.md
**Date:** 2026-02-28
**Type:** Research + audit (no code)

### What happened
Full research audit of Vince B4 (PnL Reversal Analysis panel). User referenced `BUILD-VINCE-B4-PNL-REVERSAL.md` (did not exist). Cross-referenced B2 and B3 audit docs to understand B4's inputs and upstream blockers. Found that the entire `vince/` directory did not yet exist at time of audit — B4 is blocked on B1→B2→B3.

B4 scope confirmed: single file `vince/pages/pnl_reversal.py` (~250-350 lines), pure Python, no Dash imports. Four functions: `get_pnl_reversal_analysis`, `get_tp_sweep_curve`, `get_optimal_exit_analysis`, `compute_mfe_bin`. 8 bottlenecks/questions identified, 6 improvements proposed.

Key bottleneck: Q1 — does backtester_v384 output `mfe`, `mae`, `saw_green`, `entry_atr` per trade? HIGH RISK if absent. TP sweep should simulate from MFE (not re-run backtester). ATR bin granularity: spec says 6-bin, reference says 9-bin; recommendation was 9-bin for finer resolution.

### Decisions recorded
- B4 does NOT import Dash/Plotly, re-run backtester, filter trade count, train ML models, or touch DB.
- TP sweep: simulate from MFE (if `mfe_atr >= tp_level`, trade would have hit TP).
- Recommended 9-bin ATR histogram over 6-bin spec.
- `rl_overlay: Optional[List] = None` as placeholder — real RL is future scope.

### State changes
- `BUILD-VINCE-B4-PNL-REVERSAL.md` was to be written (future step — spec not created this session).
- Plan file: `C:\Users\User\.claude\plans\concurrent-sniffing-brook.md` created.
- No code written.

### Open items recorded
- Confirm Q1/Q2 by reading `engine/position_v384.py`.
- Complete B1 → B2 → B3 before building B4.
- Write `BUILD-VINCE-B4-PNL-REVERSAL.md` spec (deferred).

### Notes
None.

---

## 2026-03-02-b2-api-types-build.md
**Date:** 2026-03-02
**Type:** Build session

### What happened
Completed B2 (Vince API Layer + Dataclasses). All 6 files created and py_compile validated: `vince/__init__.py` (12 lines), `vince/types.py` (148 lines), `vince/api.py` (185 lines), `vince/audit.py` (310 lines), `tests/test_b2_api.py` (195 lines), `scripts/build_b2_api.py` (92 lines).

`vince/types.py` contains 8 dataclasses: IndicatorSnapshot, OHLCRow, EnrichedTradeSet, MetricRow, ConstellationFilter, ConstellationResult, SessionRecord, BacktestResult. `vince/api.py` contains 8 stub functions raising `NotImplementedError` with build-block references. `vince/audit.py` has 13 checks (AST parsing, bot signal import, BBW wiring, ExitManager, interface, rot_level, version, trailing, stage2, BE raise, vince dir, SL mult, enricher).

Also built `scripts/build_strategy_analysis.py` which generates `docs/STRATEGY-ANALYSIS-REPORT.md` for pasting into Claude Web.

7 critical architecture findings documented from audit: bot runs v1 signal (not v386), BBW orphaned, ExitManager likely dead code, trailing stop divergence (backtester AVWAP vs bot 2% callback), BE raise missing from bot, rot_level=80 nearly useless, strategies/four_pillars.py v1 has wrong base class.

### Decisions recorded
- Plugin passed as per-call argument (not global) in api.py — thread-safe for Optuna.
- B2 is DONE; B1 is next (unblocks B3-B6).

### State changes
- B2 block complete: 6 files created, py_compile PASS.
- 7 critical architecture issues documented.

### Open items recorded
- Run `build_strategy_analysis.py` → paste into Claude Web.
- Discuss and fix strategy (rot_level, trailing stop, BBW wiring, bot vs backtester).
- Build B1 once strategy is correct.

### Notes
None.

---

## 2026-03-02-bingx-dashboard-v1-3-audit-and-patches.md
**Date:** 2026-03-02 (multiple sessions appended, extends to 2026-03-03)
**Type:** Audit + multiple patch build sessions

### What happened
Multi-session log covering v1-3 through v1-4 dashboard work across 2026-03-02 and into 2026-03-03.

**Early 2026-03-02:** Ran `build_dashboard_v1_3_final.py`, audited full v1-3 (1805 lines + 180 CSS), found 6 issues (duplicate import io, Unreal PnL None choke, Move SL validation blocks trailing, CB-10 State vs Input, ISO week edge case, gross_pnl alias confusion). Patch 1 fixed B1+B2+B4.

**Mid 2026-03-02:** User tested live — 5 remaining visual issues. Key root cause discovered: Dash 2.x uses CSS custom properties (CSS variables) at `:root`. Class-name CSS and `!important` do NOT override CSS variables — must override at `:root`. Patch 2 (F1+F2+F3+F4) written: status bar equity card, CSS :root variable block, equity curve with unrealized extension, position reconciliation (calls BingX API, removes stale state.json positions). Patches 3-5 applied (balance from API, date filter, stale session, coin detail, CSS improvements).

**Late 2026-03-02:** Patches 6 (CSS variables :root block) and 7 (bot status feed in main.py + dashboard polling) written. Patch 7 changes 4 files: main.py (write_bot_status), data_fetcher.py (progress_callback), dashboard (store-bot-status, status-interval, status panel), CSS (.status-feed-panel).

**v1-4 requirements received** (user AFK messages): Rename tabs, add Bot Terminal tab with Start/Stop, 6-tab layout. `build_dashboard_v1_4.py` written with 15 safe_replace patches (P1-P14). py_compile PASS.

**2026-03-03 continuation:** All 15 anchors audited against v1-3 — all PASS. User ran dashboard, crash: `DuplicateCallback: allow_duplicate requires prevent_initial_call`. Fix: `prevent_initial_call='initial_duplicate'` for CB-T3. Patch1 written. Dash skill updated to v1.3 (PART 5, 9 sections). New issues: doubled status messages (patch7 applied twice to main.py), IndexError in `flat_data[ind]` (CB-S1 and CB-T3 both on status-interval with mismatched prevent_initial_call). Patch2 written (13 patches: dedup main.py, toggle button, OFFLINE header, 360px log height). Session ended with KeyError: browser using stale callback map — fix is Ctrl+Shift+R.

### Decisions recorded
- CSS custom properties must be overridden at `:root` in Dash 2.x dark theme implementations.
- `prevent_initial_call='initial_duplicate'` fires on load AND allows duplicate registration.
- Force kill (`taskkill /F`) is instant death — no Python cleanup runs; dashboard must write stop event.
- Patch scripts must be idempotent (check if already applied before writing).

### State changes
- Multiple patch scripts written and applied: patch, patch2, patch3, patch4, patch5 (applied), patch6 (applied), patch7 (applied to main.py twice — error).
- `bingx-live-dashboard-v1-4.py` created from v1-3 + 15 patches.
- `build_dashboard_v1_4_patch1.py`: CB-T3 fix.
- `build_dashboard_v1_4_patch2.py`: Written, run status unclear at session end.
- Dash skill: v1.2 → v1.3 (PART 5 appended).

### Open items recorded
- Verify patch2 ran (check output for all 13 PASS).
- Hard refresh browser (Ctrl+Shift+R) after restart.
- Plan and build bot status feed feature.
- Version as v1-4 once all visual issues resolved (was already versioned).

### Notes
This log covers the most complex patch sequence in the project. The root cause of all white backgrounds (Dash CSS variables) was a significant discovery. Patch7 was applied twice — a process error highlighted as a lesson learned.

---

## 2026-03-03-bingx-dashboard-v1-4-patches.md
**Date:** 2026-03-03 (with 2026-03-04 continuation appended)
**Type:** Build session (multiple patches)

### What happened
Continuation of v1-4 dashboard work. Key events across multiple sessions:

**Session 1 (2026-03-03 early):** build_dashboard_v1_4.py audit confirmed all 15 anchors PASS. User ran, got CB-T3 crash (allow_duplicate without prevent_initial_call). `build_dashboard_v1_4_patch1.py` written to add `prevent_initial_call='initial_duplicate'`. Dash skill updated to v1.3 (PART 5).

New issues after patch1: Activity Log capped too small (180px), doubled status messages (patch7 applied twice), IndexError `flat_data[ind]`. Diagnosed: duplicate `write_bot_status` function in main.py. Patch2 written: 13 patches across 3 files (dedup main.py, toggle button, OFFLINE header, 360px log, CB-T3 fix to `prevent_initial_call=True`). Additional user reports: header still shows LIVE when bot stopped, no Telegram on stop (expected with force kill), Start/Stop should be single toggle.

**Session 2 (2026-03-03 afternoon):** Two bot/config changes: (1) BingX native trailing order disabled (`trailing_activation_atr_mult: null`, `trailing_rate: null`) — was conflicting with TTP engine. (2) BE raise switched from `ttp_state == "ACTIVATED"` waiting to live mark price trigger (fetches per-position every 30s). Monitor loop poll reduced 60s → 30s. `max_positions: 15`, `max_daily_trades: 200`.

**Session 3 (2026-03-03 evening):** Patch4 applied (Close Market button + CB-16 callback). 2/2 PASS, py_compile PASS, dashboard running. Patch5 written (TTP per-position controls + BE buffer): TTP Act%/Trail% inputs per position, CB-17/CB-18 for Set TTP/Activate Now, signal_engine.py TTP override handling, `be_buffer=0.001` added to position_monitor.py BE price formula. Patch5 NOT YET RUN.

**2026-03-04 continuation:** Exit mechanics fully verified from source. All 3 SL ladder steps confirmed. Patch5 confirmed already applied (be_buffer present). Monitor optimization: early return in check() when no positions in state (skip API call).

### Decisions recorded
- BingX native trailing disabled — TTP Python engine is sole trailing mechanism.
- BE raise trigger: live mark price every 30s (not 5m candle close ttp_state wait).
- BE price formula: `entry * (1 + commission_rate + 0.001)` for LONG.
- Single toggle button (Start/Stop) replaces separate Start + Stop buttons.
- force kill via taskkill /F means bot cleanup must come from dashboard, not bot.

### State changes
- Patches 1-4 applied, patch5 written (confirmed applied by 2026-03-04).
- `config.yaml`: trailing disabled, position_check_sec 30, max_positions 15, max_daily_trades 200.
- `position_monitor.py`: BE trigger rewritten, be_buffer added, early return guard added.
- SL ladder: 3 steps confirmed from code.

### Open items recorded
- Verify Close Market flow with an actual open position (awaiting test).

### Notes
Patch3 (TTP columns + Controls toggle) referenced in cumulative table but not detailed in this session — details are in the TTP integration build session.

---

## 2026-03-03-cuda-dashboard-v394-build.md
**Date:** 2026-03-03
**Type:** Build session (multiple sessions appended)

### What happened
Multi-session build log for the CUDA GPU sweep integration in dashboard v3.9.4.

**Session 1:** Spec audit via 3 parallel Explore agents found 4 issues (wrong backtester version reference, column name inconsistency, reentry cloud3 gate status, stale IndentationError claim). Build script `scripts/build_cuda_engine.py` written creating 3 files: `engine/cuda_sweep.py`, `engine/jit_backtest.py`, `scripts/dashboard_v394.py`. Python 3.13 CUDA blocker discovered: Numba 0.61.2 does not support Python 3.13 for CUDA. Python 3.12 install script written (`INSTALL-PYTHON312-CUDA.md`).

**Session 2:** Python 3.12 venv created at `.venv312`. CUDA setup required multiple fixes: nvvm.dll not found, NVCC 12.9 too new for Numba 0.64, cudart.dll not found. GPU Sweep confirmed working on 0GUSDT (top combo: SL=0.5, TP=999, BE=0.5, CD=5, 119 trades, $28,595 net PnL, PF 5.55).

**Session 3:** GPU Portfolio Sweep mode added (build script: `build_gpu_portfolio_sweep.py`). Features: multi-coin loop, coin selection (Top/Lowest/Random/Custom N), capital models (Per-Coin Independent or Shared Pool), parameter ranges, progress bar. Results display: Uniform Params, Per-Coin Optimized (labeled overfitted), heatmaps, CSV exports. Bugs fixed: ROI math, cherry-picking bias labeling, stale params detection, heatmap aggregation.

**Session 3 continued — Full Logic Audit:** 3 parallel audit agents run. CRITICAL: (1) commission fix never applied to cuda_sweep.py (still taker for both sides), (2) pnl_sum missing entry commissions. HIGH: win_rate displayed as fraction not percentage, TTP state lost on restart (later found incorrect), WSListener dies permanently after 3 reconnect failures, `_place_market_close()` missing `reduceOnly=true`, saw_green check `>` vs `>=`. 15+ total findings documented.

**Session 4 — Audit Fixes:** `build_audit_fixes.py` written. CRITICAL #1/#2: split commission rates in cuda_sweep.py (0.0008 taker entry / 0.0002 maker exit). HIGH #3: win_rate formatted as percentage. HIGH #5: WSListener MAX_RECONNECT 3→10, exponential backoff, dead flag file. HIGH #6: reduceOnly added. HIGH #7: saw_green `>` → `>=`.

**Session 5 — UX Improvements:** GPU Portfolio Sweep enhancements: coin selection reset tracking, Stop Sweep button, Reset Parameters button, date range display, Random Week/Month options, Trading Volume & Rebates stats, Est. Trade Duration. Three bugs fixed: parquet index is int64 not DatetimeIndex, bar count check, variable used before definition.

### Decisions recorded
- Engine version: Backtester390 for GPU sweep (differs from CPU sweep running v3.8.4).
- Python 3.12.8 in `.venv312`, side-by-side with system 3.13.
- CUDA toolkit via pip packages (not conda): `nvidia-cuda-nvcc-cu12==12.4.131`.
- Build approach: single build script copies v392 + applies text patches.
- Commission: taker 0.0008 entry, maker 0.0002 exit (not both taker).
- GPU Portfolio "Uniform Params" shown first (honest); "Per-Coin Optimized" labeled as overfitted upper bound.

### State changes
- 3 new files: `engine/cuda_sweep.py`, `engine/jit_backtest.py`, `scripts/dashboard_v394.py`.
- dashboard v3.9.4: LIVE, GPU sweep confirmed on RTX 3060.
- Multiple audit fixes applied to cuda_sweep.py, dashboard_v394.py, ws_listener.py, position_monitor.py.
- Dash skill: v1.2 → v1.3 (noted in v1-4-patches log, same day).

### Open items recorded
- Remaining MEDIUM/LOW findings deferred: stale detection gaps, Shared Pool capital enforcement, TTP mid-bar timing, race condition, commission fallback mismatch, slippage, close-remaining counters, UI tweaks.
- Strategy finetuning (4P stochastics, open trade scenarios) and BingX bot monitoring: next day's focus.

### Notes
HIGH #4 (TTP state lost on restart) was reassessed — code already restores TTP state via signal_engine.py lines 113-127. HIGH #6 (reduceOnly missing) was found in position_monitor.py, not executor.py (log corrected the prior assertion).

---

## 2026-03-03-cuda-dashboard-v394-planning.md
**Date:** 2026-03-03
**Type:** Planning session (no code)

### What happened
Short planning session. No code written. User asked if existing CUDA handover log (`2026-03-03-cuda-sweep-engine-handover.md`) was clear — confirmed yes. User requested a dashboard-focused spec for a new chat. Identified 4 pre-audit errors still in the old vault plan (`06-CLAUDE-LOGS/plans/2026-03-03-cuda-sweep-engine.md`): wrong column names for reentry, wrong param_grid shape, wrong TP sentinel value, missing cloud3 arrays. Wrote corrected dashboard spec as session handover.

Key architecture facts locked in spec: 12 kernel input arrays (4 price + 4 entry + 2 reentry + 2 cloud3), param_grid [N,4], tp_mult=999.0 sentinel, Welford's online variance for Sharpe, ThreadPoolExecutor workers must not call st.*, ensure_warmup() at module import, base v392 (NOT v393).

### Decisions recorded
- New spec file created to replace error-containing old vault plan.
- sweep_all_coins_v2.py deferred — not in this build.

### State changes
- System plan: `C:\Users\User\.claude\plans\synthetic-mapping-ember.md` created.
- Vault copy: `06-CLAUDE-LOGS/plans/2026-03-03-cuda-dashboard-v394-spec.md` created.

### Open items recorded
- Open new chat, paste spec, execute build.

### Notes
This planning session preceded the CUDA build session (same date) — documents the pre-build spec correction step.

---

## 2026-03-03-daily-bybit-updater.md
**Date:** 2026-03-03
**Type:** Build session

### What happened
Built a daily-run script for updating the backtester's Bybit candle data cache (399 coins, stale since 2026-02-13). Build script `scripts/build_daily_updater.py` creates `scripts/daily_update.py`.

Features of `daily_update.py`: (1) Bybit symbol discovery via `/v5/market/instruments-info` for all active USDT linear perps (~548 symbols); (2) Incremental fetch using `.meta` end timestamp per coin, fetches only the gap; (3) 5m resampling via `TimeframeResampler` from `resample_timeframes.py`; (4) Dual logging (file + console with timestamps). CLI flags: `--dry-run`, `--skip-new`, `--skip-resample`, `--max-new N`, `--months N`.

Designed as standalone script (not a patch to fetch_data.py) with different lifecycle (daily unattended vs manual bulk). py_compile PASS on build script, ast.parse PASS on embedded source. Not yet executed by user.

Multiple vault files updated: TOPIC-backtester.md, LIVE-SYSTEM-STATUS.md, PRODUCT-BACKLOG.md (C.29 added), DASHBOARD-FILES.md (v3.9.4 promoted), plan file created.

### Decisions recorded
- Standalone script, not a patch to fetch_data.py.
- Incremental append logic lives in daily_update.py (fetcher.py kept stable).
- Backlog item C.29 created for Daily Bybit Data Updater.

### State changes
- `scripts/build_daily_updater.py`: NEW, py_compile PASS.
- `scripts/daily_update.py`: created by build script, not yet executed.
- Dashboard v3.9.4 promoted to production in DASHBOARD-FILES.md.

### Open items recorded
- User to run: `python scripts/build_daily_updater.py` then `python scripts/daily_update.py --dry-run`.

### Notes
None.

---

## 2026-03-03-session-handoff.md
**Date:** 2026-03-03
**Type:** Handoff / context switch (no builds)

### What happened
Context handoff session from a prior context-limit session. Verified all B2 artefacts intact, memory files updated correctly, INDEX.md and PRODUCT-BACKLOG.md current. Wrote next-steps roadmap to `06-CLAUDE-LOGS/plans/2026-03-03-next-steps-roadmap.md`. Identified a signal file conflict in B1 spec.

B1 spec (`BUILD-VINCE-B1-PLUGIN.md`, written 2026-02-28) says to import from `signals/four_pillars_v383_v2.py`. But the v386 scoping session (2026-02-28) created `signals/four_pillars_v386.py`, and the B3 spec explicitly says it is blocked waiting on v386. Resolution: B1 must use `signals/four_pillars_v386.py`. The plan mode plan (`snuggly-mixing-moon.md`) is correct; the BUILD spec is outdated.

### Decisions recorded
- B1 must import from `signals/four_pillars_v386.py` (not v383_v2 as stated in BUILD spec).
- Follow plan mode plan for signal imports, not build spec.

### State changes
- Roadmap written: `06-CLAUDE-LOGS/plans/2026-03-03-next-steps-roadmap.md`.
- No code changes.

### Open items recorded
- Immediate first step: run `scripts/build_strategy_analysis.py` → paste into Claude Web.
- See roadmap for full prioritized list.

### Notes
Directly contradicts/updates the B1 spec from 2026-02-28 regarding which signal file to import.

---

## 2026-03-03-signal-rename-architecture-session.md
**Date:** 2026-03-03
**Type:** Architecture / scoping session (no code)

### What happened
Deep architecture analysis of the Four Pillars signal system. Read Pine Script source `four_pillars_v3_8_2_strategy.pine`, `V3.8.2-COMPLETE-LOGIC.md`, `Core-Trading-Strategy.md`, and prior session logs.

Key finding: The existing A/B/C grade naming system is architecturally incorrect. A = renamed Quad (4/4 stochs, Cloud 3 bypassed). B = renamed Rotation (3/4 stochs, Cloud 3 gated, final name TBC by Malik). C = ADD — NOT a state machine signal type; it is an engine label applied when a Quad/Rotation signal fires while a same-direction position is already open. The current Pine C signal (2/4 stochs) is wrong by design, not by parameterisation.

Gap analysis: Pine state machine generates Quad + Rotation + C (wrong — C must be removed). Python state_machine.py generates `long_signal_c` (must be removed). Python backtester assigns grade C as fresh entry fallback (wrong — ADD = engine label when same-direction position exists). Config `allow_c_trades` should be renamed `allow_add`.

5 pending questions: edit permissions on bot files (unanswered), trailing stop alignment direction (unanswered), final name for B (Malik to decide), ADD fires only on Quad/Rotation quality (awaiting confirmation), Q2.

### Decisions recorded
- A → Quad (locked).
- B → Rotation (name TBC by Malik).
- C → ADD (engine label, not state machine signal).
- ADD definition: Quad or Rotation fires while same-direction position open + capacity + cooldown met.
- C signals in Pine (2/4 stochs) must be removed entirely.

### State changes
- No files written except this session log.
- Architecture decisions documented for future implementation.

### Open items recorded
- Malik confirms ADD definition (Q5).
- Malik finalises B name (Q4).
- Q2, Q3 answers needed.
- Create `signals/state_machine_v390.py`, `signals/four_pillars_v390.py`, `engine/backtester_v390.py`.
- Update Pine script (separate session).

### Notes
None.

---

## 2026-03-03-ttp-integration-build.md
**Date:** 2026-03-03
**Type:** Build session

### What happened
Built two build scripts from the audited TTP integration plan. Read all 5 source files to be patched before writing. Confirmed `state_manager.update_position()` signature (key + updates dict with lock). Fixed unicode escape error in build script docstrings (Windows paths with `\U` trigger Python's unicode escape parser in triple-quoted strings — fix: prefix with `r"""` or use forward slashes).

`scripts/build_ttp_integration.py` — 6 patches: P1 creates `ttp_engine.py` (TTPExit class, TTPResult dataclass, run_ttp_on_trade, 5 bug fixes), P2 patches signal_engine.py (TTPExit import, ttp_config, restructured on_new_bar, _evaluate_ttp_for_symbol), P3 patches position_monitor.py (check_ttp_closes, _cancel_all_orders_for_symbol, _place_market_close, _fetch_single_position), P4 patches main.py (ttp_config pass, monitor.check_ttp_closes()), P5 patches config.yaml (ttp_enabled/ttp_act/ttp_dist), P6 creates `tests/test_ttp_engine.py` (6 unit tests).

`scripts/build_dashboard_v1_4_patch3.py` — 5 patches: TTP + Trail Lvl columns added, TTP state in positions dataframe, TTP section in Strategy Parameters tab, CB-11/CB-12 updated for TTP controls.

5 bugs fixed in ttp_engine.py (from plan): CLOSED state assignment, activation candle fall-through, CLOSED_PARTIAL replaced, iterrows replaced with itertuples, band_width_pct guard.

py_compile PASS on both build scripts.

### Decisions recorded
- Unicode escape fix: use `r"""` prefix or forward slashes in Windows path comments inside generated Python source strings.
- `itertuples(index=False)` preferred over `iterrows()` in TTPExit engine.

### State changes
- `scripts/build_ttp_integration.py`: NEW, py_compile PASS.
- `scripts/build_dashboard_v1_4_patch3.py`: NEW, py_compile PASS.
- INDEX.md and TOPIC-bingx-connector.md updated.
- NOT YET RUN by user at time of logging.

### Open items recorded
- User to run both build scripts, then pytest, then restart dashboard.

### Notes
None.
