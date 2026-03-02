# Product Backlog
**Last updated:** 2026-02-28 (v386 scoping DONE, B1 unblocked)

---

## P0 — Active / In Progress

| ID | Task | Status | Notes |
|----|------|--------|-------|
| P0.1 | Fill 256-coin period gaps (41 days) | DONE | 256/256 filled, 0 remaining |
| P0.2 | BingX connector demo live (Step 2) | PARKED | 5m demo ran 18h: 31 trades, -$379 PnL, EXIT_UNKNOWN down to 6%. VST API too unreliable for strategy validation (vanishing orders, wrong fills). Decision: let bot run locally, move focus to Vince ML. |
| P0.4 | Run BingX API docs scraper | DONE | Complete. Output: BINGX-API-V3-COMPLETE-REFERENCE.md (16KB) |
| P0.3 | Dashboard v3.9.3 indentation fix | DONE | Fixed + silent date filter fallback fixed. Promoted to production. |
| P0.5 | v386 Scoping Session | DONE | Produced `signals/four_pillars_v386.py` + `docs/FOUR-PILLARS-STRATEGY-v386.md`. Key: require_stage2=True + allow_c=False. Freq: ~93/day -> ~40/day. |
| P0.6 | Vince B1 — FourPillarsPlugin | READY | Build spec: `BUILD-VINCE-B1-PLUGIN.md`. File: `strategies/four_pillars_plugin.py`. Wraps `signals/four_pillars_v386.py`. No code written yet. |

## P1 — High Priority

| ID | Task | Status | Notes |
|----|------|--------|-------|
| P1.1 | Data contracts (research/contracts.py) | READY | Column schemas for L4->L4b->L5 boundaries |
| P1.2 | Deploy staging files (Vince ML v1) | SUPERSEDED | v1 classifier approach rejected. Staging files serve no purpose under v2 direction. |
| P1.3 | MC result caching (params_hash + parquet) | READY | Saves 23 min on re-runs |
| P1.4 | BBW per-tier reports (coin_tiers.csv needed) | READY | Run coin_classifier first, re-run CLI with tiers |
| P1.5 | WEEX Screener build (3 files) | SCOPED | Scope: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-24-weex-screener-scope.md` |
| P1.6 | Four Pillars Strategy Scoping (Step 2) | BLOCKED | 19 unknowns from `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-23-four-pillars-strategy-scoping.md` |
| P1.7 | Vince v2 concept lock + build plan | DONE | Concept locked 2026-02-27. GUI (Dash) + architecture skeleton added. Build plan: B1-B10. Next: B1 FourPillarsPlugin. |
| P1.8 | Vince B2 — API layer + types | READY after B1 | Research done 2026-02-28. Spec: `BUILD-VINCE-B2-API.md`. Files: `vince/types.py`, `vince/api.py`. |
| P1.9 | Vince B3 — Enricher | BLOCKED on v386 signal file | All 8 design decisions locked (2026-02-28). Spec updated: `BUILD-VINCE-B3-ENRICHER.md`. Unblocks when `signals/four_pillars_v386.py` exists. |

## P2 — Medium Priority

| ID | Task | Status | Notes |
|----|------|--------|-------|
| P2.1 | ML meta-label on D+R grades | BACKLOG | D=-$3.59/tr, R=-$3.00/tr, drag -$3,323 |
| P2.5 | Vince B4 — PnL Reversal panel | BLOCKED on B1->B2->B3 | Spec: `BUILD-VINCE-B4-PNL-REVERSAL.md`. Panel 2, highest priority after infrastructure ready. |
| P2.6 | Vince B5 — Query engine | BLOCKED on B1->B2->B3 | Spec: `BUILD-VINCE-B5-QUERY-ENGINE.md`. Constellation filter + permutation test. |
| P2.7 | Vince B6 — Dash shell | BLOCKED on B1->B5 | Spec: `BUILD-VINCE-B6-DASH-SHELL.md`. 8-panel multi-page app skeleton. |
| P2.2 | Multi-coin portfolio optimization | BACKLOG | Add PEPE, SAND, HYPE |
| P2.3 | 400-coin ML sweep (XGBoost) | BACKLOG | All 399 coins on 5m |
| P2.4 | Live TradingView validation | BACKLOG | Pine v3.8 vs Python backtester |

## P3 — Low Priority / Future

| ID | Task | Status | Notes |
|----|------|--------|-------|
| P3.1 | 24/7 executor framework | NOT BUILT | trading-tools/executor/ |
| P3.2 | UI/UX research for dashboard workflow | BACKLOG | |
| P3.3 | Ollama code review integration | BACKLOG | qwen2.5-coder:32b |

## Completed

| ID | Task | Date | Notes |
|----|------|------|-------|
| C.1 | Backtester v3.8.4 (production) | 2026-02-14 | Current engine in dashboard.py |
| C.2 | Dashboard v3.9.1 (production) | 2026-02-17 | 14 patches, PDF export, combined CSV export |
| C.3 | VINCE ML (9 modules) | 2026-02-14 | 37/37 tests, staging ready, NOT yet deployed |
| C.4 | Period loader + BTCUSDT gap fix | 2026-02-14 | 1.64M bars, 0 gaps |
| C.5 | Data normalizer | 2026-02-12 | 6 exchange formats |
| C.6 | Export single coin parquet | 2026-02-14 | results/trades_RIVERUSDT_5m.parquet |
| C.7 | BBW Layer 1: signals/bbwp.py | 2026-02-14 | 61/61 tests |
| C.8 | BBW Layer 2: signals/bbw_sequence.py | 2026-02-14 | 68/68 tests |
| C.9 | BBW Layer 3: research/bbw_forward_returns.py | 2026-02-14 | 102/102 tests |
| C.10 | BBW Layer 4: research/bbw_simulator.py | 2026-02-14 | 55/55 tests, 44/44 debug |
| C.11 | BBW Layer 4b: research/bbw_monte_carlo.py | 2026-02-16 | 45/45 tests, 57/57 debug, sanity PASS |
| C.12 | BBW Layer 5: research/bbw_report.py | 2026-02-16 | 58/58 tests, 11 CSVs, 30.3 KB |
| C.13 | Coin classifier (research/coin_classifier.py) | 2026-02-17 | KMeans tier assignment, 16/16 tests |
| C.14 | BBW CLI (scripts/run_bbw_simulator.py) | 2026-02-17 | L1-L5 end-to-end, 12/12 tests, smoke PASS 21.2s |
| C.15 | Ollama utility (research/bbw_ollama_review.py) | 2026-02-17 | Optional LLM review of L5 CSVs, NOT a BBW layer |
| C.16 | Dashboard v3.9.1 | 2026-02-17 | 14 patches, PDF export, combined trades CSV |
| C.17 | Dashboard v3.9.2 (production) | 2026-02-18 | Equity curve fix, capital model v2, 2500 lines |
| C.18 | BingX Connector build | 2026-02-20 | 25 files, 67/67 tests, FourPillarsV384 plugin |
| C.19 | Screener v1 | 2026-02-24 | Built but superseded (backward-looking approach) |
| C.20 | Vault organization build | 2026-02-26 | MEMORY.md split, INDEX.md, DASHBOARD-FILES.md, LIVE-SYSTEM-STATUS.md |
| C.21 | VPS migration scripts | 2026-02-26 | 3 scripts: migrate_pc.ps1, setup_vps.sh, deploy.ps1. Two audit rounds. Not yet executed. |
| C.22 | BingX demo trade analysis | 2026-02-27 | 31 trades, -$379 PnL, 6 VST API oddities documented. Decision: stop optimizing demo. Log: `06-CLAUDE-LOGS/2026-02-27-bingx-trade-analysis.md` |
| C.23 | YT Analyzer v2 | 2026-02-27 | Timestamps, clickable YouTube links, LLM summaries+tags (qwen3:8b), TOC, download stats. 6 files, all py_compile pass. |
| C.24 | BingX Live Screener | 2026-02-27 | Headless loop, FourPillarsV384 signal detection, Telegram A/B alerts, dedup by bar_ts. File: screener/bingx_screener.py |
| C.25 | BingX Daily P&L Report | 2026-02-27 | Reads trades.csv, computes today P&L+win rate+best/worst, Telegram report. Schedule via Task Scheduler at 21:00. File: scripts/daily_report.py |
| C.26 | Dashboard v3.9.3 | 2026-02-28 | Stale cache fix (clear portfolio when settings change) + silent date filter fallback fixed (7d no longer shows full year). 4 edits. Promoted to production. |
