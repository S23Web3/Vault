# BingX Automation Build — 2026-02-27

## Summary
Built two headless automation tools for the BingX connector:
1. Live signal screener — polls all 47 coins, Telegram alerts on A/B signals
2. Daily P&L report — reads trades.csv, sends Telegram digest at 5pm UTC

## Files Built

### screener/bingx_screener.py
- **Path**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\screener\bingx_screener.py`
- **Architecture**: Headless loop (60s interval), reuses FourPillarsV384 plugin directly
- **API**: Live BingX public klines (`https://open-api.bingx.com`), no auth
- **Signal detection**: Calls `plugin.get_signal(df)` — same logic as the live bot
- **Dedup**: `last_alerted = {symbol: bar_ts}` — no repeat alerts on same bar
- **Telegram**: A/B only. Format: grade, direction, ATR ratio, entry/SL/TP
- **Logging**: `logs/YYYY-MM-DD-screener.log` + console
- **py_compile**: PASS
- **Run**: `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\screener\bingx_screener.py"`

### scripts/daily_report.py
- **Path**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\daily_report.py`
- **Architecture**: One-shot script, reads trades.csv, filters to today UTC
- **Stats**: total_pnl, n_trades, win_rate, best/worst trade (symbol + pnl)
- **Telegram**: HTML format, daily digest
- **Schedule**: Task Scheduler daily at 21:00 local = 17:00 UTC
- **Logging**: `logs/YYYY-MM-DD-daily-report.log` + console
- **py_compile**: PASS
- **Run**: `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\daily_report.py"`

## Key decisions
- Reused FourPillarsV384 plugin directly (no signal code duplication)
- Fetcher copied from data_fetcher._fetch_klines() (same endpoint, retry logic, parsing)
- Live API used for screener (VST has corrupted data — public klines always from live)
- Notifier imported from notifier.py (same Telegram pattern as bot)

## Also completed today
- BingX API docs scraper: ran and produced `BINGX-API-V3-COMPLETE-REFERENCE.md` (16KB, ~215 endpoints)
- Vault updates: LIVE-SYSTEM-STATUS.md, PRODUCT-BACKLOG.md, TOPIC-bingx-connector.md

## Task Scheduler install (daily report, run as admin once)
```
schtasks /create /tn "BingXDailyReport" /tr "python \"C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\daily_report.py\"" /sc daily /st 21:00 /f
```

---

## Session 2 — UML Expansion (context continuation, same date)

### Work done
Expanded `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\docs\TRADE-UML-ALL-SCENARIOS.md` with 4 new sections:

**Section 11 — BingX Order Status States**
- All 6 BingX order statuses: NEW, PENDING_NEW, PARTIALLY_FILLED, FILLED, CANCELED, EXPIRED
- Mapped to openOrders vs allOrders visibility
- Mapped to exit detection code paths (TP_HIT / SL_HIT / EXIT_UNKNOWN)
- Auto-cancel pattern documented (BingX auto-cancels orphaned SL/TP on fill)

**Section 12 — Full Data Flow Map**
- Every API endpoint consumed (public + private) with calling function named
- Every local file read (config.yaml, state.json, .env) and written (state.json, trades.csv, logs)
- Full compute path: klines → compute_signals → get_signal → RiskGate → Executor → StateManager
- All Telegram event triggers listed with their source function

**Section 13 — Extended Scenarios (PLANNED, NOT YET BUILT)**
- Breakeven raise: trigger at 1x ATR profit, SL → entry_price, state updated, BE_HIT outcome
- Raised SL (lock profit): trigger at 2x ATR profit, SL → entry+1xATR, locks in positive PnL on SL_HIT
- Trailing TP: trigger when price exceeds current TP by trail_step, TP re-placed at market+1xATR
- Extended state machine: OPEN → BREAKEVEN_ARMED / SL_LOCKED / TP_TRAILING → CLOSED

**Section 14 — Cancel + Replace API Pattern**
- 3-step sequence: DELETE existing order → POST replacement → update state.json
- Critical failure guards: if POST fails after DELETE = no stop order = dangerous, notifier alert required

### Hard rule violation (logged)
- Violation: used relative paths `[docs/TRADE-UML-ALL-SCENARIOS.md](PROJECTS/...)` in final response
- Rule: FULL PATHS EVERYWHERE — always write full Windows path in all output
- Consequence: log + new chat per user protocol
- Correct form: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\docs\TRADE-UML-ALL-SCENARIOS.md`
