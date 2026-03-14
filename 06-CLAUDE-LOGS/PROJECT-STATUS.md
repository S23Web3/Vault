# Four Pillars Project — Current Status
*Last updated: 2026-03-14 (QuickPaste overnight build executed, Phase 0 failed).*
*Source: research orchestrator synthesis (353 files) + all session logs to 2026-03-14.*

---

## What is done and working

| Component | Version | Status |
|-----------|---------|--------|
| Python backtester | v3.8.4 | Stable. Full pipeline runs, saves to PostgreSQL. |
| BingX connector | v3 | 19 bugs fixed from v2 (race condition, TTP fallback, shallow copy, positionSide filter, step_size cache). All py_compile PASS. Template for WEEX build. |
| BingX live bot | v1.5 (v2 codebase) | Live on real money ($110 margin, 47 coins). TTP, breakeven, Telegram alerts working. |
| Trade CSV | trades_all.csv | 193 trades merged (v1 + v2 connector), 2026-03-03 to 2026-03-11. 20-column v2 schema. Location: `PROJECTS\bingx-connector-v2\trades_all.csv`. |
| BBW pipeline | layers 1-5 | Built and tested. Bollinger Band Width feature extraction complete. |
| Pine Script indicator | v3.8 | Stable on TradingView. |
| Infrastructure | — | PostgreSQL (port 5433), Ollama (qwen3:8b), CUDA configured. All operational. |
| Trade chart report | v1 | `run_trade_chart_report.py` (748 lines, py_compile PASS). 3-panel per-trade HTML. NOT YET RUNTIME-TESTED. |
| TDI module | v1 | `signals/tdi.py` (~300 lines, py_compile PASS). `compute_tdi()` → 24 columns. `compute_tdi_core()` → +8 graded signal columns (A/B/C/Rev long+short). Two presets: cw_trades (RSI 13) and classic (RSI 14, Dean Malone). Delta-based zones, regular+hidden divergence, buy/sell/best_setup signals. Standalone — NOT wired into pipeline. NOT YET RUNTIME-TESTED on real data. |
| 55/89 EMA backtester | v1 | `engine/backtester_55_89.py` built. 4-phase AVWAP SL/TP. Dashboard v3 built. |
| Vince plugin interface | base_v2.py | `strategies/base_v2.py` — StrategyPlugin ABC. Strategy-agnostic. EXISTS. |
| Vince B2 API + types | vince/ | `vince/types.py`, `vince/api.py`, `vince/audit.py`. Built 2026-03-02. py_compile PASS. No upstream data yet. |

---

## Critical Findings (2026-03-06 to 2026-03-12)

### BingX v2 → v3: 19 Bugs Fixed (2026-03-12)
- 4 CRITICAL: race condition double PnL, TTP fallback to SL price, shallow copy thread unsafety, stale timestamp on retry
- 5 HIGH: no positionSide filter, no step_size caching, commission naming confusion, silent stuck symbols, singleton base_url ignored
- 7 MEDIUM + 3 LOW: order sort, log cleanup, phantom reconcile, warmup throttle, utcnow deprecation, others
- All fixed in `PROJECTS\bingx-connector-v3\`. Use v3 as template for WEEX.

### R:R = 0.28 Root Cause CONFIRMED (2026-03-10)
- v3.8.4 state machine fires when stoch_9/14/40/60 ALL simultaneously at extreme lows (<25-30)
- Pure V-bottom reversal model — max ATR at entry, small bounce, wide SL
- S4 scored 10% alignment to core perspective
- The signal model is fundamentally wrong for the stated strategy

### 55/89 Strategy: 8/9 Coins Negative (2026-03-11)
- #1 failure mode: COUNTER_TREND (77.4% of losers entering against EMA direction)
- Grade C = 55-64% of trades, 28-30% WR — dead weight
- FARTCOINUSDT: EXCLUDE (2193 trades, 28.1% WR, -$60k)
- P0 fixes applied: sl_mult 4.0, avwap_warmup 20. Validated on AXSUSDT only.

### S12 Cloud Role Corrected (2026-03-11)
- Cloud is NOT an entry signal or filter
- Cloud = macro context + TP target (Cloud 3 midband) + SL movement ONLY
- Entry is fired by stoch_60 and tier-specific triggers

### WEEX: No Historical OHLCV (2026-03-12)
- All kline params silently ignored. Returns latest ~1000 candles only.
- Decision: Bybit as backtesting proxy, BingX data for non-Bybit coins
- WEEX = Bitget white-label (API structure, symbol format, URL paths match exactly)
- 8-phase build plan approved. Handoff prompt written. No code built.

---

## Vince Status — UNBLOCKED (redesigned 2026-03-12)

### Architecture Decision (locked 2026-03-12)
Vince is **fully strategy-independent**. It analyses any trade CSV from any strategy. The Four Pillars plugin is one example. B1 no longer waits for V4.

**What Vince answers (priority order):**
1. **Exit timing** — when to hold vs cut, based on indicator state after entry (let winners run, cut losers)
2. **Entry quality** — which indicator constellations at entry produce the best outcomes
3. **TP optimisation** — what TP multiple maximises net PnL per strategy, per coin

**Data source for B1:** `trades_all.csv` — 193 live bot trades, 20 columns. Available now.

### Build chain

| Block | Component | Status |
|-------|-----------|--------|
| B1 | Vince core + generic plugin interface | **READY TO BUILD** — unblocked. `base_v2.py` ABC exists. Runs on `trades_all.csv` immediately. |
| B2 | API layer + types | BUILT (2026-03-02) — py_compile PASS. Stubs only. |
| B3 | Enricher (`vince/enricher.py`) | READY after B1. Attaches indicator snapshots to every trade row. |
| MARKOV | Indicator State Transition Engine | READY after B3. `vince/markov.py`. 16-state composite (stoch_60 × stoch_40). Transition matrix per coin. Continuation prob + reversal risk at 3/5/10 bars. 9 columns added per trade. |
| B4 | PnL Reversal — Panel 2 ★ PRIORITY | READY after B1→B2→B3→MARKOV. MFE histogram, TP sweep, state heatmap, prob decay curve. |
| B5 | Constellation query engine | READY after B1→B2→B3. |
| B6 | Dash shell | READY after B1→B5. |
| B7–B10 | Discovery, Optimizer, Validation, remaining panels | Blocked on B1→B6. |

### What B1 requires to build
- `strategies/base_v2.py` — EXISTS
- `trades_all.csv` (193 trades, 20 cols) — EXISTS
- `signals/four_pillars_v383_v2.py` — EXISTS (compute_signals for enricher)
- `engine/backtester_v384.py` — EXISTS (run_backtest for plugin)
- Python skill + Dash skill — load at session start

### Multi-strategy plugin interface
Any strategy implementing `StrategyPlugin` ABC works with Vince:
- `compute_signals(ohlcv_df)` → enriched DataFrame
- `parameter_space()` → sweepable params with bounds
- `trade_schema()` → column definitions for this strategy's trade CSV
- `run_backtest(params, start, end, symbols)` → Path to trade CSV
- `strategy_document` → Path to strategy markdown (for LLM layer)

Future strategies (V4, 55/89, WEEX) plug in without changing Vince core.

---

## QuickPaste Project — Separate Repo Status

**What:** Open-source Windows 11 text expander. TypeItIn replacement. Rust + SendInput (zero clipboard), egui UI, system tray.
**Repo:** `C:\Users\User\Documents\quickpaste\` (separate from Obsidian Vault)
**Tech:** Rust (edition 2021, target x86_64-pc-windows-msvc), `windows` crate 0.58+, `tray-icon` 0.19, `egui` 0.29, `embed-resource` 3.0+

| Component | Status | Notes |
|-----------|--------|-------|
| setup_rust.ps1 | Built + Fixed | 6 steps (MSVC check, Rust install, toolchain, rust-analyzer, git init). ASCII-only, MSVC linker filter added. Fixes 8 audit issues. |
| build_quickpaste.py | Built + Working | Overnight autonomous orchestrator. 6 phases, each calls `claude -p` + `cargo verify`. 9pm countdown timer + live progress bar. |
| Rust skill | Built | `C:\Users\User\.claude\skills\rust\SKILL.md` — complete, referenced in all phase prompts. |
| Phase 0 (Scaffold) | **FAILED** | Overnight build 2026-03-13 17:00 UTC failed at Phase 0. Error not logged. Debug: `--phase 0` or `--dry-run`. |
| Phases 1-5 | NOT STARTED | Blocked on Phase 0 fix. |

**Next:** Debug Phase 0 failure, retry build.

---

## V4 Strategy Status — PRIMARY FOCUS

**Goal:** R:R >= 1.0 at 50% WR. Rebates = bonus.
**Approach:** Chart-driven design. No code until strategy is verbally expressed, visually confirmed, user-approved.

| Phase | Status |
|-------|--------|
| 1. Data collection | IN PROGRESS — trade chart report built. Bot on 47 coins. |
| 2. Pattern discovery | NOT STARTED — needs 20+ annotated trades |
| 3. Strategy expression | NOT STARTED |
| 4. Visual confirmation | NOT STARTED |
| 5. User approval | NOT STARTED |
| 6. V4 build | BLOCKED — no code until Phase 5 |

**V4 code does not exist:** `state_machine_v4.py`, `four_pillars_v4.py`, `backtester_v4.py` — none started.

---

## Built but not verified

- GPU sweep v3.9.4 — CUDA backtester, never validated for CPU parity
- GPU sweep 5589 — `cuda_sweep_5589.py` py_compile PASS, not runtime-tested
- 55/89 full portfolio sweep — P0 params validated on AXSUSDT only, full sweep not done
- Trade chart report — py_compile PASS, never runtime-tested
- Vince B2 API — py_compile PASS, no upstream data yet
- Rebate reconciliation — logic written, not confirmed against exchange data
- VPS error recovery — not tested under failure conditions
- WEEX connector — Phase 2+3 artifacts exist (Sonnet-built, Opus-audited, 4 critical fixes applied). Phase 2 executed: 700 perp contracts indexed, 532 have local backtest data (Bybit preferred, BingX fallback), 168 WEEX-only. Phase 4 blocked on API keys.

---

## Not started (biggest gaps)

- **V4 signal model** — chart-driven analysis in progress. No code until approved.
- **Vince B1** — READY TO BUILD. First deliverable: Vince core + plugin interface on `trades_all.csv`.
- Walk-forward optimisation
- Risk circuit breaker
- n8n alert-to-bot webhooks
- CI/CD, monitoring, automated backups
- Vince B3–B10

---

## Decisions locked

1. Commission: 0.08% taker per side on notional
2. Stochastics: 9/14/40/60 Raw K (smooth=1)
3. Ripster Cloud numbering: 2=5/12, 3=34/50, 4=72/89, 5=180/200
4. Timeframe: 5m beats 1m on all low-price coins
5. Vince role: Research Engine (parameter optimiser), NOT a trade classifier
6. Dashboard: Dash (not Streamlit)
7. Signal grading: A/B/C entry tiers
8. TTP: native trailing stop with ATR activation
9. LSG baseline: 85-92% of losers were profitable at some point — TP/ML filter is the key lever
10. Tight TP hurts: TP < 2.0 ATR damages most coins
11. Cloud role: macro context + TP + SL movement ONLY — NOT entry signal or filter (2026-03-11)
12. V4 approach: chart-driven design, no code until user approves (2026-03-12)
13. Vince independence: strategy-agnostic core. Four Pillars is one plugin example. (2026-03-12)
14. Vince data source: `trades_all.csv` (193 live bot trades) as B1 input. (2026-03-12)
15. Vince primary intelligence order: (1) exit timing, (2) entry quality, (3) TP optimisation. (2026-03-12)
16. WEEX connector = original code for open-source GitHub submission. BingX v2 = architecture reference only. v3 = separate project. (2026-03-12)
17. Markov chain layer = future side build (P3.10). No dependency on B1-B6. Scoping session required before build. Does not block current work. (2026-03-12)

---

## Open decisions

- V4 signal model (cascade? hierarchical? stoch_60-primary?)
- TDI inclusion in V4 signal pipeline (module now available: `signals/tdi.py` with `compute_tdi_core()` graded signals)
- Channel gate and two-cycle divergence in V4
- Stoch 55 as trigger (never implemented)
- Walk-forward window sizes for Vince Mode 3
- Which coins to scale live bot to
- TTP exact parameter values per coin
- Ollama/local LLM role in Vince pipeline
- Markov chain state space design (which indicators, how many states, discretisation boundaries) — prerequisite for scoping session when ready
- BBW integration path into backtester signals
- Dynamic position sizing logic
- Screener architecture (WEEX vs BingX)

---

## One-line summary

Live bot on 47 coins with confirmed wrong signal model (R:R=0.28). V4 design in chart-driven analysis phase. Vince redesigned as fully strategy-independent — B1 unblocked, builds on 193 live trades immediately, no dependency on V4.
