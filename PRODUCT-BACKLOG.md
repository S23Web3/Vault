# Product Backlog
**Last updated:** 2026-03-12 session 2 (Vince redesigned strategy-independent — B1 unblocked, B3/B4/B5 unblocked cascade, BingX v3 built, WEEX planned)

---

## P0 — Active / In Progress

| ID | Task | Status | Notes |
|----|------|--------|-------|
| P0.7 | Strategy V4 — chart-driven design | IN PROGRESS | Trade chart report built (748 lines, py_compile PASS). Bot on 47 coins. User annotates trades. No V4 code until verbally expressed, visually confirmed, user-approved. |
| P0.8 | Runtime-test trade chart report | READY | `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\scripts\run_trade_chart_report.py" --date 2026-03-12`. Unblocks V4 pattern discovery. |
| P0.9 | WEEX Connector build | READY | 8-phase plan approved. Handoff prompt: `06-CLAUDE-LOGS\plans\2026-03-12-weex-connector-build-prompt.md`. Use BingX v3 as template. New chat required. |
| **P0.10** | **Vince B1 — Vince core + generic plugin interface** | **READY TO BUILD** | **Redesigned 2026-03-12. Strategy-agnostic. Runs on `trades_all.csv` (193 live trades) immediately. No V4 dependency. Four Pillars is one example plugin. New Claude Code session required.** |
| P0.1 | Fill 256-coin period gaps | DONE | 256/256 filled |
| P0.2 | BingX connector demo live | PARKED | Demo API unreliable. Bot running on real account. |
| P0.3 | Dashboard v3.9.3 fix | DONE | Silent date filter fallback fixed. Production. |
| P0.4 | BingX API docs scraper | DONE | BINGX-API-V3-COMPLETE-REFERENCE.md (16KB) |
| P0.5 | v386 Scoping Session | DONE | `four_pillars_v386.py` + `FOUR-PILLARS-STRATEGY-v386.md`. require_stage2=True + allow_c=False. |
| P0.6 | Vince B1 (old framing — FourPillarsPlugin) | SUPERSEDED by P0.10 | Was blocked on V4. Now redesigned — Vince is strategy-agnostic, B1 builds core + interface. |

---

## P1 — High Priority

| ID | Task | Status | Notes |
|----|------|--------|-------|
| P1.10 | 55/89 full portfolio sweep (P0 params) | READY | sl_mult=4.0, avwap_warmup=20. Validated on AXSUSDT only. Full sweep pending. |
| P1.11 | V4 pattern discovery session | BLOCKED on P0.8 | Needs 20+ annotated trades from chart report tool. |
| P1.12 | Vince B3 — Enricher | READY after P0.10 (B1) | Attaches indicator snapshots to every trade row. 8 design decisions locked. |
| P1.13 | Vince B4 — PnL Reversal Panel ★ PRIORITY | READY after P0.10→B2→B3 | MFE histogram in ATR bins, TP sweep, answers "when to hold vs cut". |
| P1.14 | Vince B5 — Constellation query engine | READY after P0.10→B2→B3 | Filter + delta logic. Entry quality analysis. |
| P1.1 | Data contracts (research/contracts.py) | READY | Column schemas for L4→L4b→L5 |
| P1.3 | MC result caching | READY | Saves 23 min on re-runs |
| P1.4 | BBW per-tier reports | READY | Run coin_classifier first |
| P1.5 | WEEX Screener | SUPERSEDED by P0.9 | Full connector replaces screener-only |
| P1.6 | Four Pillars Strategy Scoping Step 2 | SUPERSEDED | Subsumed by V4 design work |
| P1.7 | Vince v2 concept lock + build plan | DONE | Concept locked 2026-02-27. B1-B10 plan. |
| P1.8 | Vince B2 — API layer + types | DONE | Built 2026-03-02. py_compile PASS. Stubs only. |
| P1.9 | Vince B3 — Enricher (old framing) | SUPERSEDED by P1.12 | Same deliverable, now unblocked from V4. |

---

## P2 — Medium Priority

| ID | Task | Status | Notes |
|----|------|--------|-------|
| P2.7 | Vince B6 — Dash shell | READY after B1→B5 | `vince/app.py` + `vince/layout.py`. Sidebar, routing, all panels wired. |
| P2.8 | Vince B7 — Panels 1,3,4,5 | BLOCKED on B6 | Coin Scorecard, Constellation UI, Exit State, Trade Browser. |
| P2.9 | Vince B8 — Mode 2 Auto-Discovery | BLOCKED on B7 | XGBoost feature importance + k-means clustering. |
| P2.10 | Vince B9 — Mode 3 Settings Optimizer | BLOCKED on B7 | Optuna parameter sweep, Calmar ratio fitness. |
| P2.11 | Vince B10 — Validation + Session History | BLOCKED on B9 | Monte Carlo p-values, walk-forward, session history panel. |
| P2.1 | ML meta-label on D+R grades | BACKLOG | D=-$3.59/tr, R=-$3.00/tr |
| P2.2 | Multi-coin portfolio optimisation | BACKLOG | |
| P2.3 | 400-coin ML sweep (XGBoost) | BACKLOG | |
| P2.4 | Live TradingView validation | BACKLOG | Pine v3.8 vs Python backtester |

---

## P3 — Low Priority / Future

| ID | Task | Status | Notes |
|----|------|--------|-------|
| P3.1 | 24/7 executor framework | NOT BUILT | |
| P3.2 | UI/UX research for dashboard | BACKLOG | |
| P3.3 | Ollama code review integration | BACKLOG | qwen2.5-coder:32b |
| P3.4 | VPS autostart for BingX bot | NOT BUILT | Linux systemd or tmux |
| P3.5 | Vince RL Exit Policy Optimizer | FUTURE | Panel 2 overlay. Separate scoping session required. |
| P3.10 | Vince Markov Chain Layer | FUTURE — side build | State-space transition model on indicator states. Answers: given indicator state at entry, probability of continuation vs reversal at each bar forward. Slots into Panel 2 overlay + optional standalone panel. Build after B4 is verified. Separate scoping session required — state space definition, indicator selection, transition matrix build. No dependency on B1-B6. |
| P3.6 | Vince LLM Interpretation (Panel 9) | FUTURE | Ollama layer. Separate scoping session required. |
| P3.7 | V4 plugin for Vince | FUTURE | Once V4 is approved and built, add as second StrategyPlugin. |
| P3.8 | 55/89 plugin for Vince | FUTURE | Third StrategyPlugin. Same Vince core, zero changes. |
| P3.9 | WEEX plugin for Vince | FUTURE | Fourth StrategyPlugin once WEEX connector live. |

---

## Completed

| ID | Task | Date | Notes |
|----|------|------|-------|
| C.45 | Vince strategy-independence redesign | 2026-03-12 | B1 unblocked. Multi-strategy plugin architecture locked. trades_all.csv as B1 input. |
| C.46 | BingX connector v3 build | 2026-03-12 | 19 bugs fixed. All py_compile PASS. Template for WEEX. |
| C.47 | trades_all.csv merge | 2026-03-12 | 193 trades (v1+v2), 20-col v2 schema. Vince B1 input. |
| C.30 | Trade chart report tool | 2026-03-12 | 748 lines. py_compile PASS, not runtime-tested. |
| C.31 | WEEX API probe | 2026-03-12 | NO historical OHLCV confirmed. Bybit as proxy. |
| C.32 | S12 cloud role correction | 2026-03-11 | Cloud NOT entry. Context + TP + SL only. |
| C.33 | 55/89 negative coin analysis | 2026-03-11 | 8/9 coins negative. COUNTER_TREND 77.4%. FARTCOIN excluded. |
| C.34 | Strategy V4 research | 2026-03-10 | S4=10% alignment. R:R=0.28 root cause confirmed. |
| C.35 | 55/89 trade analysis + P0 fixes | 2026-03-10 | sl_mult 4.0, avwap_warmup 20. AXSUSDT: Sharpe 3.085. |
| C.36 | GPU sweep 5589 | 2026-03-10 | py_compile PASS, not runtime-tested. |
| C.37 | v1/v2 mechanical fixes | 2026-03-06 | 16/16 patches. allOrders-first, place-then-cancel BE/SL. |
| C.38 | BingX v2 live deployment | 2026-03-06 | 250 files pushed, e85b370. Bot self-sufficient. |
| C.39 | 55/89 engine + dashboard v3 | 2026-03-07 | Engine + dashboard built. GPU toggle, PDF export. |
| C.40 | Strategy catalogue + visualizer | 2026-03-07 | 5 strategies documented. visualize_strategy_perspectives.py. |
| C.41 | BingX v2 live stats analysis | 2026-03-07 | 38 trades, 65.8% WR, R:R=0.28. |
| C.42 | BingX data pipeline | 2026-03-05 | 626 coins fetcher + daily updater + scheduler. |
| C.43 | Native trailing stop build | 2026-03-05 | ttp_mode toggle. Eliminates ~6min TTP delay. |
| C.44 | Research orchestrator | 2026-03-05 | 353 files, 22 batches, 1.2h. PROJECT-STATUS.md created. |
| C.1–C.29 | Earlier work (Feb) | 2026-02 | See INDEX.md |
