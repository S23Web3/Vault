# Product Backlog
**Last updated:** 2026-03-12 (V4 chart-driven workflow, WEEX connector planned, trade chart report built)

---

## P0 — Active / In Progress

| ID | Task | Status | Notes |
|----|------|--------|-------|
| P0.7 | Strategy V4 — chart-driven design | IN PROGRESS | Trade chart report tool built (748 lines, py_compile PASS). Bot running on 47 coins. User reviews charts, annotates trades, identifies patterns. No V4 code until strategy is verbally expressed, visually confirmed, and user-approved. |
| P0.8 | Runtime-test trade chart report | READY | `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\scripts\run_trade_chart_report.py" --date 2026-03-12`. First runtime test pending. |
| P0.9 | WEEX Connector build | READY | 8-phase architecture approved. Handoff prompt: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-12-weex-connector-build-prompt.md`. API probe confirmed NO historical OHLCV. Needs new chat. |
| P0.1 | Fill 256-coin period gaps (41 days) | DONE | 256/256 filled, 0 remaining |
| P0.2 | BingX connector demo live (Step 2) | PARKED | 5m demo ran 18h: 31 trades, -$379 PnL. VST API too unreliable. Decision: let bot run locally, move to Vince. |
| P0.3 | Dashboard v3.9.3 indentation fix | DONE | Fixed + silent date filter fallback fixed. Promoted to production. |
| P0.4 | Run BingX API docs scraper | DONE | Complete. Output: BINGX-API-V3-COMPLETE-REFERENCE.md (16KB) |
| P0.5 | v386 Scoping Session | DONE | Produced `signals/four_pillars_v386.py` + `docs/FOUR-PILLARS-STRATEGY-v386.md`. Key: require_stage2=True + allow_c=False. |
| P0.6 | Vince B1 — FourPillarsPlugin | BLOCKED on V4 | Was "READY". Now blocked: V4 signal model must be defined first. B1 defines what ML model learns — can't use v3.8.4 signal (proven wrong). |

## P1 — High Priority

| ID | Task | Status | Notes |
|----|------|--------|-------|
| P1.10 | 55/89 full portfolio sweep (P0-fixed params) | READY | sl_mult=4.0, avwap_warmup=20. Validated on AXSUSDT (40.7% WR, Sharpe 3.085). Full sweep on all coins not yet done. |
| P1.11 | V4 pattern discovery session | BLOCKED on P0.8 | Joint session after user has 20+ annotated trades from chart report tool. |
| P1.1 | Data contracts (research/contracts.py) | READY | Column schemas for L4->L4b->L5 boundaries |
| P1.3 | MC result caching (params_hash + parquet) | READY | Saves 23 min on re-runs |
| P1.4 | BBW per-tier reports (coin_tiers.csv needed) | READY | Run coin_classifier first, re-run CLI with tiers |
| P1.5 | WEEX Screener build (3 files) | SUPERSEDED by P0.9 | Full connector replaces screener-only approach |
| P1.6 | Four Pillars Strategy Scoping (Step 2) | SUPERSEDED | 19 unknowns from scoping session — now subsumed by V4 design work |
| P1.7 | Vince v2 concept lock + build plan | DONE | Concept locked 2026-02-27. Build plan: B1-B10. |
| P1.8 | Vince B2 — API layer + types | DONE | Built 2026-03-02. All py_compile PASS. |
| P1.9 | Vince B3 — Enricher | BLOCKED on V4 -> B1 | All 8 design decisions locked. Blocked until V4 signal model exists. |

## P2 — Medium Priority

| ID | Task | Status | Notes |
|----|------|--------|-------|
| P2.1 | ML meta-label on D+R grades | BACKLOG | D=-$3.59/tr, R=-$3.00/tr, drag -$3,323 |
| P2.5 | Vince B4 — PnL Reversal panel | BLOCKED on B1->B2->B3 | |
| P2.6 | Vince B5 — Query engine | BLOCKED on B1->B2->B3 | |
| P2.7 | Vince B6 — Dash shell | BLOCKED on B1->B5 | |
| P2.2 | Multi-coin portfolio optimization | BACKLOG | |
| P2.3 | 400-coin ML sweep (XGBoost) | BACKLOG | |
| P2.4 | Live TradingView validation | BACKLOG | Pine v3.8 vs Python backtester |

## P3 — Low Priority / Future

| ID | Task | Status | Notes |
|----|------|--------|-------|
| P3.1 | 24/7 executor framework | NOT BUILT | trading-tools/executor/ |
| P3.2 | UI/UX research for dashboard workflow | BACKLOG | |
| P3.3 | Ollama code review integration | BACKLOG | qwen2.5-coder:32b |
| P3.4 | VPS autostart for BingX bot | NOT BUILT | Needs Linux systemd or tmux. |

## Completed

| ID | Task | Date | Notes |
|----|------|------|-------|
| C.30 | Trade chart report tool | 2026-03-12 | `bingx-connector-v2/scripts/run_trade_chart_report.py` (748 lines). 3-panel Plotly HTML per trade. py_compile PASS, not runtime-tested. |
| C.31 | WEEX API probe | 2026-03-12 | `scripts/probe_weex_api.py`. Confirmed NO historical OHLCV. Decision: Bybit as proxy. |
| C.32 | S12 cloud role correction | 2026-03-11 | Cloud is NOT entry signal/filter. Corrected in `S12-MACRO-CYCLE.md`. |
| C.33 | 55/89 negative coin analysis | 2026-03-11 | 8/9 coins negative. COUNTER_TREND 77.4%. Grade C 55-64% at 28-30% WR. FARTCOIN excluded. |
| C.34 | Strategy V4 research | 2026-03-10 | S1-S11 scored. S4=10% (pile-in). Root cause of R:R=0.28 confirmed. 5 decisions pending. |
| C.35 | 55/89 trade analysis + P0 fixes | 2026-03-10 | 6 flaws found. sl_mult 2.5->4.0, avwap_warmup 5->20. AXSUSDT validation: Sharpe 3.085. |
| C.36 | GPU sweep 5589 | 2026-03-10 | cuda_sweep_5589.py. py_compile PASS, not runtime-tested. |
| C.37 | v1/v2 mechanical fixes | 2026-03-06 | 16/16 patches applied. allOrders-first exit, place-then-cancel BE/SL, configurable be_buffer. |
| C.38 | BingX v2 live deployment | 2026-03-06 | Full vault push (250 files, e85b370). Bot self-sufficient on VPS. |
| C.39 | 55/89 engine + dashboard v3 | 2026-03-07 | Backtester5589 engine (4-phase AVWAP SL/TP). Dashboard v3 (re-roll seed, shared pool, GPU toggle, PDF export). |
| C.40 | Strategy catalogue + visualizer | 2026-03-07 | 5 strategies documented (Bible, v3.8.1, v3.8.4, BingX v1.5, 55/89). visualize_strategy_perspectives.py. |
| C.41 | BingX v2 live stats analysis | 2026-03-07 | 38 trades, 65.8% WR, R:R=0.28. Capital analysis at $500/20x. |
| C.42 | BingX data pipeline | 2026-03-05 | Bulk fetcher (626 coins), daily updater, autorun scheduler. All py_compile PASS. |
| C.43 | Native trailing stop build | 2026-03-05 | ttp_mode toggle, _cancel_open_sl_orders bug fix. Eliminates ~6min TTP delay. |
| C.44 | Research orchestrator | 2026-03-05 | `run_log_research.py`. 22/22 batches, 353 files, 1.2h. PROJECT-STATUS.md created. |
| C.1 | Backtester v3.8.4 (production) | 2026-02-14 | Current engine in dashboard.py |
| C.2 | Dashboard v3.9.1 (production) | 2026-02-17 | 14 patches, PDF export, combined CSV export |
| C.3 | VINCE ML (9 modules) | 2026-02-14 | 37/37 tests, staging ready, NOT yet deployed |
| C.4 | Period loader + BTCUSDT gap fix | 2026-02-14 | 1.64M bars, 0 gaps |
| C.5 | Data normalizer | 2026-02-12 | 6 exchange formats |
| C.6 | Export single coin parquet | 2026-02-14 | results/trades_RIVERUSDT_5m.parquet |
| C.7-C.12 | BBW Layers 1-5 + Monte Carlo | 2026-02-14 to 2026-02-16 | All tests passing |
| C.13 | Coin classifier | 2026-02-17 | KMeans tier assignment, 16/16 tests |
| C.14 | BBW CLI | 2026-02-17 | L1-L5 end-to-end, smoke PASS 21.2s |
| C.15 | Ollama utility | 2026-02-17 | Optional LLM review of L5 CSVs |
| C.16-C.17 | Dashboard v3.9.1-v3.9.2 | 2026-02-17 to 2026-02-18 | Equity curve fix, capital model v2 |
| C.18 | BingX Connector build | 2026-02-20 | 25 files, 67/67 tests |
| C.19-C.29 | Various (screener, VPS, YT, etc.) | 2026-02-24 to 2026-03-03 | See INDEX.md for details |
