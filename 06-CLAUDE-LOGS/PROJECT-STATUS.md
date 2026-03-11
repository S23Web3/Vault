# Four Pillars Project — Current Status
*Last updated: 2026-03-10 (trade analysis session). Generated from research orchestrator synthesis (353 files, 140+ session logs). Status wired to MEMORY.md — visible in Claude Code + Claude Desktop.*

---

## What is done and working

| Component | Version | Status |
|-----------|---------|--------|
| Python backtester | v3.8.4 | Stable. Full pipeline runs, saves to PostgreSQL. |
| BingX live bot | v1.5 | Live on real money ($110 margin). TTP, breakeven, Telegram alerts working. |
| BBW pipeline | layers 1-5 | Built and tested. Bollinger Band Width feature extraction complete. |
| Pine Script indicator | v3.8 | Stable on TradingView. |
| Infrastructure | — | PostgreSQL (port 5433), Ollama (qwen3:8b), CUDA configured. All operational. |

---

## Built but not verified

- **GPU sweep (v3.9.4)** — CUDA version of backtester written, never validated for parity with CPU results
- **GPU sweep 5589** — cuda_sweep_5589.py written (2026-03-10), 4-phase AVWAP kernel matching Backtester5589. py_compile PASS but never runtime-tested (CUDA only in .venv312)
- **55/89 P0 param fixes** — sl_mult 2.5->4.0, avwap_warmup 5->20 applied to dashboard_55_89_v3.py defaults. Validated on AXSUSDT (40.7% WR, Sharpe 3.085). Full portfolio sweep with new params NOT yet done.
- **Multi-coin bot stress test** — BingX bot handles multiple coins in code, never stress-tested
- **Vince B2 API** — Flask API built but has no upstream data to feed it (blocked by B1)
- **Rebate reconciliation** — Logic written, never confirmed against real settlement data
- **VPS error recovery** — Not tested under failure conditions

---

## Not started (biggest gaps)

- **Vince B1 (Phase 0 — strategy alignment)** — THE primary blocker. Defines what features the ML model learns. Nothing in B3-B10 can start until B1 is done.
- Walk-forward optimization
- Risk circuit breaker (max drawdown stop)
- n8n alert-to-bot webhooks (TradingView → bot)
- Multi-exchange support
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

---

## Open decisions

- Vince B1 feature set (what goes into the ML model)
- Walk-forward window sizes
- Which coins to scale to
- TTP exact parameter values
- Ollama/local LLM role in the pipeline
- BBW-to-backtester integration path
- Dynamic position sizing logic
- Screener architecture (WEEX vs BingX)

---

## One-line summary

Working backtester + live bot. ML pipeline (Vince) stalled because B1 (strategy alignment — what does the model learn?) has never been started.
