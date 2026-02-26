# Product Backlog
**Last updated:** 2026-02-26

---

## P0 — Active / In Progress

| ID | Task | Status | Notes |
|----|------|--------|-------|
| P0.1 | Fill 256-coin period gaps (41 days) | DONE | 256/256 filled, 0 remaining |
| P0.2 | BingX connector demo live (Step 1) | RUNNING | 67/67 tests, bot on VST demo, 47 coins. `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main.py"` |
| P0.3 | Dashboard v3.9.3 indentation fix | BLOCKED | IndentationError at line 1972. Fix script needs rework. |

## P1 — High Priority

| ID | Task | Status | Notes |
|----|------|--------|-------|
| P1.1 | Data contracts (research/contracts.py) | READY | Column schemas for L4->L4b->L5 boundaries |
| P1.2 | Deploy staging files (Vince ML) | READY | `python scripts/build_staging.py` |
| P1.3 | MC result caching (params_hash + parquet) | READY | Saves 23 min on re-runs |
| P1.4 | BBW per-tier reports (coin_tiers.csv needed) | READY | Run coin_classifier first, re-run CLI with tiers |
| P1.5 | WEEX Screener build (3 files) | SCOPED | Scope: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-24-weex-screener-scope.md` |
| P1.6 | Four Pillars Strategy Scoping (Step 2) | BLOCKED | 19 unknowns from `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-23-four-pillars-strategy-scoping.md` |
| P1.7 | Vince v2 plugin interface spec | WAITING | Concept v2 approved. Next: formal plugin interface spec. |

## P2 — Medium Priority

| ID | Task | Status | Notes |
|----|------|--------|-------|
| P2.1 | ML meta-label on D+R grades | BACKLOG | D=-$3.59/tr, R=-$3.00/tr, drag -$3,323 |
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
