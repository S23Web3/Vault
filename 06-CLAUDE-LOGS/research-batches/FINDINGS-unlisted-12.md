# Batch Findings — Unlisted-12
**Processed:** 2026-03-06
**Files:** 20

---

## 2026-02-14-bbw-layer3-prompt-build.md
**Date:** 2026-02-14
**Type:** Build session

### What happened
Two parallel work streams completed: (1) Python skill updated with unicode escape prevention after a `SyntaxError` caused by Windows backslash paths (`\Users`) in docstrings triggering Python's 32-bit Unicode escape parser. Skill files updated at three locations. New sections added: String & Encoding Safety (Windows), Pre-Execution Validation (mandatory `py_compile`), Code Review Checklist items. (2) Layer 3 (Forward Return Tagger) build prompt created at `BUILDS\PROMPT-LAYER3-BUILD.md`. Scope: 6 files including `research/bbw_forward_returns.py` with 17 output columns (8 per window × 2 + ATR). Two full bug audit passes conducted: 10 bugs total (3 critical, 4 high, 3 medium), all fixed. Critical fixes: changing 5-bar datasets to 20-bar with appropriate atr_period, fixing "exact 3.0 ATR" impossibility in tests, correcting hand-computed ATR values when entry bar had different range than warmup bars. Final stable ATR=4.0, max_up_atr=1.75, max_down_atr=1.75, max_range_atr=3.5.

### Decisions recorded
- Unicode escape prevention mandatory in all future Python builds
- Mandatory `python -m py_compile` after every file write
- Layer 3 prompt file: `BUILDS\PROMPT-LAYER3-BUILD.md`
- Python skill renamed from `python-trading-development.md` to `python-trading-development-skill.md`

### State changes
- Layer 3 build prompt created and double-audited (10 issues fixed)
- Python skill updated at 3 locations with unicode escape prevention + pre-execution validation

### Open items recorded
- Layer 3 prompt ready for execution in Claude Code (not yet executed)

### Notes
Layer 2 was already COMPLETE at 68/68 PASS — no changes this session.

---

## 2026-02-14-bbw-layer5-build-prompt.md
**Date:** 2026-02-14
**Type:** Build session / Planning

### What happened
Layer 5 (BBW Report Generator) build prompt created and audited. Layer 5 is the CSV report formatter — it takes Layer 4 (SimulatorResult) and optional Layer 4b (MonteCarloResult) output and writes organized CSVs. Read Layer 4 prompt, architecture doc, and prior session logs before writing the spec. Output structure: `reports/bbw/aggregate/` (7 CSVs), `optimal/` (LSG grid), `scaling/`, optional `monte_carlo/` and `per_tier/` sections, plus `report_manifest.csv` and `simulation_metadata.csv`. 15 audit issues found (3 HIGH, 6 MEDIUM, 6 LOW) — all fixed or documented. HIGH fixes: architecture signatures missing `config` param, `_summarize_group` crashes on all-NaN expectancy_usd, mock n_triggered can exceed n_entry_bars. Files to be created by Claude Code: `research/bbw_report.py`, tests, debug, sanity, and orchestrator scripts. Pipeline status at session time: Layers 1-3 complete, Layer 4/5/6 build prompts ready, Layer 4b not yet prompted.

### Decisions recorded
- L5 formats only, does NOT recompute statistics
- Duck-typed validation — mocks work without importing Layer 4
- `low_sample` flag added but NOT filtered — Layer 6 decides trust
- `sensitivity/` deferred to CLI runner
- `per_tier/` conditional on coin_classifier being built
- MC section produces 0 files until Layer 4b built — by design

### State changes
- `BUILDS\PROMPT-LAYER5-BUILD.md` created and audited
- `06-CLAUDE-LOGS\2026-02-14-bbw-layer5-audit.md` created

### Open items recorded
- Execute Layer 4 first, then Layer 5
- Build order: Layer 4 → Layer 4b → Layer 5 → Layer 6

### Notes
None.

---

## 2026-02-14-bbw-layer6-build-prompt.md
**Date:** 2026-02-14
**Type:** Build session / Planning

### What happened
Layer 6 (Ollama LLM Interpretation) build prompt created and audited. Layer 6 is the terminal layer — it passes Layer 5 CSV reports to an Ollama LLM and generates 4 markdown interpretation files in `reports/bbw/ollama/`: state_analysis.md, feature_recommendations.md, anomaly_flags.md, executive_summary.md. The executive_summary.md contains BBW_LSG_MAP Python dict, feature pruning list, and scaling recommendations for handoff to live system. 8 audit issues found (1 HIGH, 4 MEDIUM, 3 LOW) — all actionable fixes applied. Also applied 15 remaining Layer 5 audit fixes during this session. 20 tests all mock Ollama (no real LLM calls in test suite). File: `research/bbw_ollama_review.py` with OllamaConfig, OllamaResult, `review_layer_code()` utility, skip flags per step.

### Decisions recorded
- All L6 tests mock Ollama — test suite runs without any LLM
- Graceful degradation: Ollama down → OllamaResult with errors, no crash
- No data transformation — L6 passes CSV text as-is to LLM
- Prompts hardcoded in source code (not external files)
- Layer 6 is the TERMINAL layer — no L7/L8 planned

### State changes
- `BUILDS\PROMPT-LAYER6-BUILD.md` created (new)
- `BUILDS\PROMPT-LAYER5-BUILD.md` modified (15 audit fixes applied)
- `06-CLAUDE-LOGS\2026-02-14-bbw-layer5-audit.md` created
- `06-CLAUDE-LOGS\2026-02-14-bbw-layer6-audit.md` created

### Open items recorded
- L6 → live system handoff: executive_summary.md → signals/four_pillars.py and ml/features.py
- Build order: Layer 4 → Layer 4b (build prompt needed) → Layer 5 → Layer 6

### Notes
None.

---

## 2026-02-14-core-build-2.md
**Date:** 2026-02-14
**Type:** Build session / Test results

### What happened
Tested and validated 9 files generated by `scripts/build_all_specs.py` (77K, generated Feb 13). Specs: SPEC-A (Dashboard v3), SPEC-B (Backtester v385), SPEC-C (VINCE ML). All 90 tests passed, zero failures, zero patches needed. Results: test_v385.py 37/37 (12 new metrics, 6 entry-state fields, lifecycle fields, LSG categories, parquet, v384 PnL match diff=0.0000); test_dashboard_v3.py 16/16 (file structure, 6 tabs, required functions, Edge Quality, presets, sweep stop); test_vince_ml.py 37/37 (coin_features 10 features, VinceModel forward pass, pool split A~60%/B~20%/C~20%, XGBoost auditor, SHAP). Functional run on RIVERUSDT 5m: 2,645 trades, 52 metrics, net_pnl=$-2,435.96. Parquet: 2,645 rows × 43 cols. Period loader BTCUSDT: 41-day gap (2025-01-01 to 2025-02-11) found and filled (59,041 bars from Bybit). Final: 1,640,574 total bars, 0 gaps >2 days, 0 duplicates.

### Decisions recorded
- v385 confirmed backward compatible with v384 (PnL diff=0.0000)

### State changes
- 9 files validated (backtester_v385, dashboard_v3, 4 ML files, 3 test scripts)
- `data/periods/2024-2025/BTCUSDT_1m.parquet` extended from 527,041 to 586,081 bars
- `results/trades_RIVERUSDT_5m.parquet` created (2,645 rows × 43 cols)

### Open items recorded
None stated.

### Notes
None.

---

## 2026-02-14-layer1-bugfix.md
**Date:** 2026-02-14 (13:07 UTC)
**Type:** Build session / Bug fixes

### What happened
5 bugs fixed in BBW Layer 1 (`signals/bbwp.py`). Bug 1+6: `_spectrum_color` rewritten — NaN→None, 4 colors at 25/50/75 (orange dropped). Bug 7: `_detect_states` warmup gap — split NaN check so bars with valid bbwp but NaN MA now detect states. Bug 8: `_percentrank_pine` NaN tolerance — count valid values, `min(lookback//2)`. Bug 5: VWMA silent fallback — added `warnings.warn()`. Bug 2: Dead NaN override — removed redundant `.loc[]` assignments. 4 tests updated (Tests 3, 5, 7 revised; Test 12 NEW for warmup gap consistency). Final: 67/67 PASS (up from 61/61). Sanity check: 32,762 RIVERUSDT 5m bars, 0.33s, 99,621 bars/sec. State distribution 12-18% across all 7 states.

### Decisions recorded
- Spectrum uses 4 colors only (blue/green/yellow/red) — orange permanently removed
- NaN bbwp → None spectrum (not a color string)

### State changes
- `signals/bbwp.py` — 5 bugs fixed
- Tests 3, 5, 7 updated; Test 12 added
- `scripts/sanity_check_bbwp.py` updated (5 → 4 colors)
- Layer 1 test count: 61 → 67

### Open items recorded
None.

### Notes
Previous count was 61/61; after this session 67/67 (new test added plus renumbering).

---

## 2026-02-14-vault-sweep-fixes.md
**Date:** 2026-02-14
**Type:** Audit / Code review

### What happened
Verified all bug claims from Qwen 14B vault sweep of 234 files (sweep 1) and a second sweep of 62 files (sweep 2, vault_sweep_4.py). Only 1 real bug was found across both sweeps. Real fix: `indicators/supporting/atr_position_manager_v1.pine` — `i_secret` webhook secret was in TradingView alert JSON payload. Fixed by removing `i_secret` from alert body and recommending URL-based auth instead. All other claims were false positives: Qwen confused SL direction for LONG/SHORT (LONG SL should be `c - 2*s` not above entry), misread early-return pattern `!= 0` as inverted, flagged division-by-zero where guards already existed, treated `>` vs `>=` design choices as bugs, and inconsistently rated identical code in v382 RED and v383 GREEN. Sweep 2: 42 RED flagged, 0 actionable bugs (100% false positive rate).

### Decisions recorded
- Qwen 14B useful for identifying files to check, not for actual bug analysis (~96% false positive rate)
- Webhook secrets must NOT appear in TradingView alert JSON payloads

### State changes
- `indicators/supporting/atr_position_manager_v1.pine`: `i_secret` removed from alert JSON (security fix — only real change from both sweeps)

### Open items recorded
None.

### Notes
Single real finding across both sweeps was the webhook secret. Sweep 2 had 100% false positive rate.

---

## 2026-02-14-vault-sweep-manifest.md
**Date:** 2026-02-14
**Type:** Other (codebase inventory)

### What happened
Manifest of 62 active Python files generated by vault_sweep_4.py. Lists each file with: why included, modification date, line count, function names, imports, and import dependencies. Files span: data layer (fetcher.py 252L, normalizer.py 542L, period_loader.py 123L), engine (backtester v382-v385, position v382-v384, commission.py, metrics.py, avwap.py), ML (coin_features, features_v2, training_pipeline, vince_model, xgboost_auditor), signals (four_pillars v382/v383, state_machine v382/v383), scripts (30+ scripts — dashboards, sweeps, test scripts, download scripts), vault-level sweep scripts. Most heavily imported: `signals/four_pillars_v383.py` (18 files). Largest script: `build_all_specs.py` at 2,190 lines. Dashboard evolution: v1 at 1,498 lines, v2 at 1,533 lines, v3 at 704 lines (significantly leaner).

### Decisions recorded
None.

### State changes
Document only — no code changes.

### Open items recorded
None.

### Notes
Snapshot document of codebase at Feb 14. Useful as a reference point for dependency mapping.

---

## 2026-02-26-vps-migration-gitignore.md
**Date:** 2026-02-26
**Type:** Build session / Infrastructure

### What happened
Vault-level `.gitignore` created (60 lines, excludes ~33GB data + secrets + runtime artifacts). BingX connector `.gitignore` updated (added `logs/`, `venv/`). `migrate_pc.ps1` patched to skip `.gitignore`/`.gitattributes` creation if files already exist (using `Test-Path`). Cross-platform verification: all bot code uses `Path(__file__).resolve()` — no hardcoded Windows paths. Plugin import path on VPS resolves to `/root/vault/PROJECTS/four-pillars-backtester`. GitHub repo confirmed as `S23Web3/Vault` (private). Vault `.gitignore` is more comprehensive than what the migration script would have created — covers entire `data/` dir, `Books/`, entire `.obsidian/`, `*.parquet`, `state.json`, `trades.csv`.

### Decisions recorded
- Cooldown (3 bars) skipped pending evaluation after 5m demo data
- 1m losses expected — 5m >> 1m for low-price coins
- GitHub repo: `S23Web3/Vault` (not `S23Web3/obsidian-vault`)

### State changes
- `C:\Users\User\Documents\Obsidian Vault\.gitignore` created (new)
- `PROJECTS\bingx-connector\.gitignore` updated
- `scripts\migrate_pc.ps1` patched

### Open items recorded
1. Run migrate_pc.ps1
2. Upload + run setup_vps.sh on VPS
3. Bot starts on VPS: systemd, 5m, 47 coins
4. Wait ~40h then run audit_bot.py
5. Audit should show TP_HIT/SL_HIT instead of EXIT_UNKNOWN

### Notes
None.

---

## 2026-02-26-vps-setup-and-autostart.md
**Date:** 2026-02-26
**Type:** Build session / Infrastructure / Deployment

### What happened
VPS setup Part B completed on `root@76.13.20.191` (Jakarta, Indonesia, Hostinger AS47583). All 9 setup steps completed: SSH key, vault clone (992 objects, 20.79 MiB to `/root/vault`), Python 3.12.3 + venv + deps installed, .env created, import test 12/12 OK, systemd service started. Critical discovery: BingX demo/VST API (`open-api-vst.bingx.com`) is blocked from VPS — 100% packet loss. Live API (`open-api.bingx.com`) via CloudFront CDN works fine (BTC price OK, auth confirmed, futures wallet $0.00). Pivoted to local Task Scheduler autostart. Built 3 new files (run_bot.ps1, bingx-bot-task.xml, install_autostart.ps1) and reformatted Telegram messages to HTML bold headers + line breaks in executor.py, position_monitor.py, main.py. All py_compile PASS. Task Scheduler "BingXBot" task registered. Bot running locally with 47 coins, 5m, demo mode. Bug: setup_vps.sh checks `BINGX_SECRET` but bot expects `BINGX_SECRET_KEY` — non-blocking cosmetic warning.

### Decisions recorded
- VPS can only run live trading (VST blocked from datacenter IPs)
- Local PC runs demo mode via Task Scheduler
- Telegram format: HTML bold headers + line breaks

### State changes
New: `scripts/build_autostart_and_tg.py`, `scripts/run_bot.ps1`, `scripts/bingx-bot-task.xml`, `scripts/install_autostart.ps1`
Modified: `executor.py`, `position_monitor.py`, `main.py` (TG formatting, all py_compile PASS)

### Open items recorded
- Stop VPS bot service: `systemctl stop bingx-bot`
- VPS ready for live when: funds in futures wallet + config.yaml `demo_mode: false`

### Notes
VPS IP `76.13.20.191` is live production infrastructure. setup_vps.sh has a variable name mismatch (`BINGX_SECRET` vs `BINGX_SECRET_KEY`) — non-blocking.

---

## 2026-02-27-bingx-bot-live-improvements.md
**Date:** 2026-02-27
**Type:** Build session

### What happened
11-step improvement session for BingX connector, plus critical post-build bug fix. Used Ollama qwen2.5-coder:14b for code generation. Steps: (1) executor.py — SL direction validation + fill_price from avgPrice. (2) position_monitor.py — commission_rate=0.0016 parameter. (3) main.py — startup commission fetch. (4) Pytest: 2 failures from FIX-3 mock data → fixed → 67/67. (5) ws_listener.py NEW — WebSocket daemon, listenKey lifecycle, ORDER_TRADE_UPDATE, fill_queue, reconnect (max 3 attempts), websockets v16.0 installed. (6-7) main.py + position_monitor.py patched for WS integration. (8) 67/67. (9) Cooldown 3 bars × 300s = 15min + 101209 retry (halved qty) + session-block mechanism across state_manager, risk_gate, signal_engine, executor, config. (10) scripts/reconcile_pnl.py NEW — PnL audit vs BingX positionHistory. (11) 67/67. Post-build critical bug: commission_rate and fill_queue used BEFORE definition in main.py — NameError at runtime. Fixed by reordering. Tests had not caught this (PositionMonitor mocked).

### Decisions recorded
- Commission rate: 0.0016 default (parameterized)
- Cooldown: 3 bars × 300s = 15 minutes
- 101209: retry with halved qty, session-block on failure
- Method names differ from plan: `add_session_blocked/is_session_blocked`, `ws_logger=logger`, `cooldown_bars + bar_duration_sec`

### State changes
Modified: executor.py, position_monitor.py, main.py, state_manager.py, risk_gate.py, signal_engine.py, config.yaml, tests/test_executor.py
New: ws_listener.py (156L), scripts/reconcile_pnl.py (148L)
All backups created (.bak). 67/67 tests throughout.

### Open items recorded
- `_handle_close_with_price()` near-copy of `_handle_close()` — must keep in sync
- ws_listener only handles TP/SL fills — add trailing stop type if needed later

### Notes
Critical bug: variable ordering in main.py would have caused NameError at runtime. Tests passed because PositionMonitor is mocked in tests — real integration not covered by tests.

---

## 2026-02-28-bingx-trade-analysis.md
**Date:** 2026-02-28
**Type:** Other (live trading performance report)

### What happened
Trade analysis report generated by analyze_trades.py. Run period: 2026-02-27 15:20 UTC to 2026-02-28 12:18 UTC. Account $110.0. Config: $5 margin × 10x = $50 notional/trade. 46 closed trades, 6 open positions at report time. Closed P&L: -$8.49. Mark-to-market: -$2.83 (-2.6%). 0 TP_HIT exits from 46 closed trades. 17 SL-at-entry exits cost $0.91 gross ($0.45 net after rebate). Best open: VIRTUAL-USDT SHORT +$3.34 unrealized (+66.8% margin ROI). Worst closed loss: AIXBT-USDT SHORT -$0.87. Best-case (all trailing TPs hit): +$2.95. Worst-case (all SLs hit): -$9.59. Bot fix applied 2026-02-28: SL raises now use entry ±0.10% (not exact entry).

### Decisions recorded
- BE+fees correction: SL raise = entry ±0.10% (not exact entry)

### State changes
Report only — BE+fees fix applied to bot same day.

### Open items recorded
6 open positions still live at report time.

### Notes
The 0 TP_HIT from 46 closed trades is expected for trailing TP systems — positions must stay open to win. Gains were in the 6 open positions.

---

## 2026-03-02-bingx-trade-analysis.md
**Date:** 2026-03-02
**Type:** Other (live trading performance report)

### What happened
Second analyze_trades.py report on same 46-trade dataset. Generated 2026-03-02 12:51 UTC. All 6 previously-open positions now closed — 0 open positions. All scenarios now identical at -$8.49 (-7.7% of $110 account). The trailing TPs on the 6 open positions (best-case +$2.95 per Feb 28 report) did not trigger — all closed at break-even or SL. Trade data identical to Feb 28 report otherwise: same 46 trades, same grade/direction breakdown, same SL-at-entry analysis, avg hold time 55m.

### Decisions recorded
None new.

### State changes
Report only.

### Open items recorded
None.

### Notes
Contradicts the best-case scenario from 2026-02-28 report: 6 open positions that showed unrealized gains all closed at or below entry, leaving final P&L at -$8.49. Bot was apparently stopped between 2026-02-28 and 2026-03-02.

---

## 2026-03-03-codebase-measurement.md
**Date:** 2026-03-03
**Type:** Other (codebase metrics)

### What happened
Python codebase size measured (excluding .venv312). Results: 421 files, 142,935 lines of code. Compared to Feb 24 baseline: files 330 → 421 (+91), lines ~66,000 estimated → 142,935 actual (+76,935). Feb 24 was an estimate at 200 lines/file avg — now confirmed actual. Human effort estimate (no AI): solo senior ~7.6 years, team of 3 ~2.5 years, team of 5 ~18 months, +20-30% for crypto/ML/API domain. By directory: scripts 136, ml 19, engine 17, signals 17, tests 16, research 10, strategies 9, utils 9, optimizer 7.

### Decisions recorded
None.

### State changes
Measurement document only.

### Open items recorded
None.

### Notes
File contains encoding issues (replacement characters visible for arrows/emojis in original content).

---

## 2026-03-03-cuda-sweep-engine-handover.md
**Date:** 2026-03-03
**Type:** Planning / Handover

### What happened
Full CUDA/GPU sweep engine plan designed and audited — no code written. Plan audited against actual source files (`backtester_v390.py`, `state_machine_v390.py`) — 18 gaps found and resolved. Context ~80% at session end; implementation deferred to new chat. Problem: sweeps fully sequential and CPU-bound (single coin 50–100s, 400 coins 6–60h). Solution: Numba `@cuda.jit`, one GPU thread per param combo, 1,980–2,112 simultaneous threads, expected ~13 minutes for 400 coins. Files to create: `engine/cuda_sweep.py`, `engine/jit_backtest.py`, `scripts/sweep_all_coins_v2.py`, `scripts/dashboard_v394.py`. Architecture verified: 12 kernel inputs (not 10) including reentry_long/reentry_short and cloud3_ok_long/short; param grid [N,4]; tp_mult=999.0 sentinel (not 0.0); Welford's online variance for Sharpe; direction conflict gate; Numba `cuda.local.array(4, numba.float32)` syntax. Dashboard v394 based on v392 (NOT v393 — has IndentationError). Known simplifications: fixed ATR SL only (no AVWAP ratcheting), no scale-outs, no ADD entries.

### Decisions recorded
- Numba CUDA over PyTorch (stateful bar-by-bar loop, not differentiable)
- tp_mult=999.0 sentinel (not 0.0 — instant exit)
- v394 base = v392 (v393 IndentationError)
- ThreadPoolExecutor workers must NOT call st.*
- `ensure_warmup()` at module import to prevent 1-5s first-run freeze
- 4 new files created via `scripts/build_cuda_engine.py` build script

### State changes
- Plan written: `C:\Users\User\.claude\plans\majestic-conjuring-meerkat.md` + vault copy
- No code written

### Open items recorded
- Implementation in new chat
- Build order: Python skill → read source files → write build_cuda_engine.py → user runs → verify CUDA → test
- Update TOPIC-backtester.md, TOPIC-dashboard.md, LIVE-SYSTEM-STATUS.md after build

### Notes
Audit issue #1: column names are `reentry_long/reentry_short` not `re_long/re_short`. v393 has a known IndentationError — v392 is the correct base.

---

## 2026-03-03-ttp-logic.md
**Date:** 2026-03-03
**Type:** Planning / Build session

### What happened
TTP (Trailing Take Profit) engine logic session — completed three nuance decisions and produced an Opus build brief. Decisions finalized: gap handling, granularity, OHLC ambiguity (details in `research/ttp-lewest.md`). Static audit of draft `ttp_engine.py` found 5 bugs: HIGH (1) self.state never set to CLOSED, HIGH (2) activation candle range not evaluated after activation fires; MEDIUM (3) CLOSED_PARTIAL state — remove, use booleans instead, MEDIUM (4) iterrows() — replace with enumerate(itertuples()), MEDIUM (5) band_width_pct None fallback misleading. Files produced: `research/ttp-lewest.md` (decisions locked), `BUILD-TTP-ENGINE.md` (Opus build brief). Opus assigned to create: `exits/ttp_engine.py`, `tests/test_ttp_engine.py`, `exits/__init__.py`.

### Decisions recorded
- CLOSED_PARTIAL state removed — use booleans instead
- iterrows() forbidden — use enumerate(itertuples())
- Three nuance decisions locked in ttp-lewest.md
- TTP engine in `exits/` subdirectory structure

### State changes
- `research/ttp-lewest.md` updated with locked decisions
- `BUILD-TTP-ENGINE.md` created (Opus build brief)

### Open items recorded
- Opus to build exits/ttp_engine.py, tests/test_ttp_engine.py, exits/__init__.py
- 5 bugs to fix during Opus build

### Notes
None.

---

## 2026-03-04-strategy-v391-failed-attempt.md
**Date:** 2026-03-04
**Type:** Session log / Failure record / Post-mortem

### What happened
Failed build attempt for strategy v391. User asked to "work on strategy v385" (clarified: next version after v390 = v391), then asked to "outlay all the parts" meaning show layout and discuss before building. Agent instead ran explore agents, asked clarifying questions, entered plan mode, wrote plan, then built 4 files without user ever confirming trading rules. User stated spec docs may be incomplete/wrong due to prior chart readings that were skipped or incorrect. Files written (syntax clean, trading logic unverified): `signals/clouds_v391.py`, `signals/four_pillars_v391.py`, `engine/position_v391.py`, `engine/backtester_v391.py`, `scripts/build_strategy_v391.py`. These exist on disk as unverified drafts.

### Decisions recorded
- LESSON: "Outlay all the parts" = stop, list current layout, wait for feedback — do NOT plan or build
- Spec docs are not sufficient as sole source of truth when user says prior chart readings were missed/wrong

### State changes
- 5 draft files created (flagged as unverified trading logic, DO NOT TREAT AS CORRECT)

### Open items recorded
- Correct process: show layout → user confirms/corrects each part → reference chart screenshots → design → explicit approval → build

### Notes
Explicit process failure record. This documents an agent behavior that the user explicitly rejected.

---

## 2026-03-05-native-trailing-build.md
**Date:** 2026-03-05
**Type:** Build session

### What happened
BingX native trailing stop (`TRAILING_STOP_MARKET` with `priceRate=0.003`) implemented as config toggle. Prior session confirmed exchange accepts this. Investigation: custom TTP engine has ~6min delay (5m candle wait + 45s poll + 30s position check). Critical bug found during scoping: `_cancel_open_sl_orders` would cancel native trailing orders because `"STOP" in "TRAILING_STOP_MARKET"` is True (substring match). Fix included in build. Built `scripts/build_native_trailing.py` which creates `PROJECTS/bingx-connector-v2/` as full copy with 6 patched files + config. Changes per file: executor.py (native trailing placement), signal_engine.py (skips TTP engine in native mode), position_monitor.py (TRAILING_EXIT detection, trailing order protection, gated TTP methods), ws_listener.py (TRAILING_STOP_MARKET WebSocket fill detection), state_manager.py (TRAILING_EXIT in trades.csv), config.yaml (ttp_mode: native). Build script py_compile PASS.

### Decisions recorded
- Config toggle: `ttp_mode: "native"` vs `"engine"` — switchback trivial
- Reuses existing `ttp_act` (0.008) and `ttp_dist` (0.003) for both modes
- BE raise stays active in native mode (safety net +0.4% to +0.8%)
- SL tighten + TTP engine skipped in native mode
- New exit reason: `TRAILING_EXIT` (distinct from SL_HIT and TTP_EXIT)
- Output: `bingx-connector-v2/` (separate copy, not overwrite)

### State changes
- `scripts/build_native_trailing.py` created (py_compile PASS)
- `06-CLAUDE-LOGS/plans/2026-03-05-native-trailing-switch.md` created
- `bingx-connector-v2/` created when user runs script (git status confirms it was run)

### Open items recorded
- User to run: `python scripts/build_native_trailing.py`

### Notes
`"STOP" in "TRAILING_STOP_MARKET"` Python substring match gotcha — order type string check was too broad.

---

## 2026-03-05-research-orchestrator-build.md
**Date:** 2026-03-05
**Type:** Build session

### What happened
Built `run_log_research.py` — Python orchestrator for automated chronological vault log research via sequential `claude -p` CLI calls. Designed for unattended overnight execution. Architecture: scans `06-CLAUDE-LOGS/` + plans, categorizes ~353 files (160 ordered, 39 unlisted, 69 dated plans, 85 auto-generated). 20 files/batch, mega files isolated, 21 file batches + 1 synthesis = 22 total. Execution: `type prompt_file.txt | claude.cmd -p --allowedTools ... --model sonnet` (shell=True). Synthesis uses opus. 6 bugs fixed: return value tuple mismatch, duplicate exclusion entry, bare `claude` not in PATH, `shell=False` cannot run .cmd on Windows, stdin pipe not forwarding (switched to temp file), duplicate log output (propagate=False). Batch 1 (20 files, 2025-01-21 to 2026-02-03) completed at 19:49:40. Pausing 1500s before batch 2.

### Decisions recorded
- Batch size: 20 files; pause: 1500s (25 min)
- Max retries: 2; retry backoff 900s; rate limit backoff 1800s
- Batch timeout: 7200s (2h); max turns: 150 normal / 80 mega / 100 synthesis
- Research model: sonnet; synthesis model: opus
- Resume logic: skip batches where FINDINGS-*.md exists AND all files checked off

### State changes
- `PROJECTS/four-pillars-backtester/scripts/run_log_research.py` created
- `06-CLAUDE-LOGS/RESEARCH-PROGRESS.md` created (353 files tracked)
- Batch 1 complete — FINDINGS-ordered-01.md written, 20 files checked off

### Open items recorded
- Batches 2-22 pending (overnight run)
- To restart from scratch: delete RESEARCH-PROGRESS.md and all research-batches/ files

### Notes
This is the orchestrator that spawned the current batch research task. The current agent is running within the infrastructure built by this session.
