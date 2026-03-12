# Four Pillars Project — Current Status
*Last updated: 2026-03-12. Generated from research orchestrator synthesis (353 files, 140+ session logs) + manual updates. Status wired to MEMORY.md — visible in Claude Code + Claude Desktop.*

---

## What is done and working

| Component | Version | Status |
|-----------|---------|--------|
| Python backtester | v3.8.4 | Stable. Full pipeline runs, saves to PostgreSQL. |
| BingX live bot | v1.5 | Live on real money ($110 margin, 47 coins). TTP, breakeven, Telegram alerts working. |
| BBW pipeline | layers 1-5 | Built and tested. Bollinger Band Width feature extraction complete. |
| Pine Script indicator | v3.8 | Stable on TradingView. |
| Infrastructure | — | PostgreSQL (port 5433), Ollama (qwen3:8b), CUDA configured. All operational. |
| Trade chart report | v1 | `run_trade_chart_report.py` (748 lines, py_compile PASS). 3-panel per-trade HTML report with stochastics, EMA 55/89, AVWAP, Four Pillars signals, comment boxes. NOT YET RUNTIME-TESTED. |
| 55/89 EMA backtester | v1 | `engine/backtester_55_89.py` built. 4-phase AVWAP SL/TP. Dashboard v3 built. |

---

## Critical Findings (2026-03-10 to 2026-03-12)

### R:R = 0.28 Root Cause CONFIRMED
- v3.8.4 state machine requires stoch_9/14/40/60 ALL in extreme (<25-30) SIMULTANEOUSLY
- This is the opposite of cascade — fires on V-bottoms (max ATR, max volatility)
- S4 scored 10% alignment to core trading perspective
- The current signal model is fundamentally wrong for the stated strategy

### 55/89 Strategy: 8/9 Coins Negative
- `analyze_negative_coins_5589.py` ran on 9 coins with P0-fixed params
- #1 failure mode: COUNTER_TREND (77.4% of losers entering against EMA direction)
- Grade C = 55-64% of trades at 28-30% WR — drag on portfolio
- FARTCOINUSDT: EXCLUDE (2193 trades, 28.1% WR, -$60k)
- Top fixes identified: EMA alignment gate, Grade C filter, Phase 2 AVWAP check

### S12 Cloud Role Corrected (2026-03-11)
- Cloud is NOT an entry signal or filter
- Cloud = macro context + TP setting (Cloud 3 midband) + SL movement ONLY
- Entry is fired by stoch_60 and tier-specific triggers

### WEEX Connector (2026-03-12)
- WEEX has NO historical OHLCV API (params silently ignored, latest ~1000 candles only)
- Decision: Bybit as backtesting proxy, BingX data for non-Bybit coins
- 8-phase architecture plan approved, handoff prompt written

---

## V4 Strategy Status — PRIMARY FOCUS

**Goal:** At least breakeven V4 (R:R >= 1.0 at 50% WR, rebates = bonus).

**Approach:** Chart-driven design. Understanding first, build never until approved.

| Phase | Status | Description |
|-------|--------|-------------|
| 1. Data collection | IN PROGRESS | Trade chart report tool built. Bot running on 47 coins. User reviews charts and annotates trades. |
| 2. Pattern discovery | NOT STARTED | Joint session: categorize user annotations into entry/exit/timing/missed signal patterns |
| 3. Strategy expression | NOT STARTED | Write V4 rules in plain English backed by trade evidence |
| 4. Visual confirmation | NOT STARTED | Create visuals proving written logic matches reality |
| 5. User approval | NOT STARTED | User explicitly says "build it" before any code |
| 6. V4 build | BLOCKED | No code until Phase 5 approval |

**Strategy docs exist but are NOT approved for build:**
- `C:\Users\User\Documents\Obsidian Vault\02-STRATEGY\STRATEGY-V4-DESIGN.md` — hybrid stochastic model, parameters drafted, backtest tables blank
- `C:\Users\User\Documents\Obsidian Vault\02-STRATEGY\S12-MACRO-CYCLE.md` — 5-tier entry architecture, stoch_60-primary, most evolved

**V4 code that does NOT exist yet:**
- `state_machine_v4.py` — not started
- `four_pillars_v4.py` — not started
- `backtester_v4.py` — not started
- TDI indicator — not built (may or may not be needed)

---

## Built but not verified

- **GPU sweep (v3.9.4)** — CUDA version of backtester written, never validated for parity with CPU results
- **GPU sweep 5589** — cuda_sweep_5589.py written (2026-03-10), 4-phase AVWAP kernel matching Backtester5589. py_compile PASS but never runtime-tested (CUDA only in .venv312)
- **55/89 P0 param fixes** — sl_mult 2.5->4.0, avwap_warmup 5->20 applied to dashboard_55_89_v3.py defaults. Validated on AXSUSDT (40.7% WR, Sharpe 3.085). Full portfolio sweep with new params NOT yet done.
- **Trade chart report** — `run_trade_chart_report.py` py_compile PASS, never runtime-tested
- **Multi-coin bot stress test** — BingX bot handles multiple coins in code, never stress-tested
- **Vince B2 API** — Flask API built but has no upstream data to feed it (blocked by B1)
- **Rebate reconciliation** — Logic written, never confirmed against real settlement data
- **VPS error recovery** — Not tested under failure conditions
- **WEEX connector** — 8-phase architecture plan approved, handoff prompt written, no code built

---

## Not started (biggest gaps)

- **V4 signal model** — THE primary blocker. Current v3.8.4 signal is fundamentally wrong (pile-in, not cascade). V4 design exists on paper but needs chart-driven validation before any build.
- **Vince B1 (Phase 0 — strategy alignment)** — Blocked until V4 signal model is defined. Defines what features the ML model learns.
- Walk-forward optimization
- Risk circuit breaker (max drawdown stop)
- n8n alert-to-bot webhooks (TradingView -> bot)
- Multi-exchange support (WEEX planned, architecture approved)
- CI/CD, monitoring, automated backups
- Vince B3-B10 (all ML phases)

---

## Decisions locked (do not revisit)

1. Commission: 0.08% taker per side on notional
2. Stochastics: 9/14/40/60 Raw K (smooth=1)
3. Ripster Cloud numbering: 2=5/12, 3=34/50, 4=72/89, 5=180/200
4. Timeframe: 5m beats 1m on all low-price coins
5. Vince role: Research Engine (parameter optimizer), NOT a trade classifier
6. Dashboard: Dash (not Streamlit)
7. Signal grading: A/B/C entry tiers
8. TTP: native trailing stop with ATR activation
9. LSG baseline: 85-92% of losers were profitable at some point — TP/ML filter is key lever
10. Tight TP hurts: TP < 2.0 ATR damages most coins
11. Cloud role: macro context + TP + SL movement ONLY — NOT entry signal or filter (corrected 2026-03-11)
12. V4 approach: chart-driven design, understanding first, no code until user approves (locked 2026-03-12)

---

## Open decisions

- V4 signal model (what fires the entry — cascade? hierarchical? stoch_60-primary?)
- Whether TDI is needed in the signal pipeline
- Channel gate and two-cycle divergence inclusion in V4
- Stoch 55 as trigger (per Core-Trading-Strategy.md v2 — never implemented anywhere)
- Vince B1 feature set (blocked until V4 defined)
- Walk-forward window sizes
- Which coins to scale to
- TTP exact parameter values
- Ollama/local LLM role in the pipeline
- BBW-to-backtester integration path
- Dynamic position sizing logic
- Screener architecture (WEEX vs BingX)

---

## One-line summary

Live bot running on 47 coins with wrong signal model (R:R=0.28). V4 strategy being designed through chart-driven analysis — trade chart report tool built, awaiting first runtime test and user trade annotations before any V4 code is written.
