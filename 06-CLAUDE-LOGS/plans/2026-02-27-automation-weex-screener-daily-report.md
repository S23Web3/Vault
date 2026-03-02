# Plan: Proper Automation — 2026-02-27

## Context
BingX demo validated. Scraper complete (BINGX-API-V3-COMPLETE-REFERENCE.md, 16KB). Bot infrastructure is solid. The current gap: the bot trades but there is NO feedback loop — no way to see what signals are setting up in real-time, no automated daily performance digest. "Proper automation" means closing that loop without human intervention.

## What automation is actually missing

| Gap | Impact | Solution |
|-----|--------|----------|
| Can't see live signal state across 100+ WEEX coins | Miss setups, no situational awareness | WEEX Live Screener |
| Performance analysis requires manual CSV reads | Daily review is manual work | Automated daily P&L Telegram report |
| Scraper completed — vault stale | LIVE-SYSTEM-STATUS shows BUILT NOT RUN | Vault update (minor) |

## The Build: 3 parallel agents

### Agent 1 — WEEX Screener data layer
**Files:**
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\screener\weex_fetcher.py`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\screener\weex_screener_engine.py`

**weex_fetcher.py** — Public WEEX API (no auth, no rate limit concern):
- `get_contracts()` → list of symbol dicts (symbol, contractSize, status)
- `get_klines(symbol, interval, limit)` → DataFrame (open, high, low, close, volume)
- Symbol format: `BTC_USDT` on WEEX public API. Interval: `1Min`, `5Min`, `1Hour`
- Endpoints: `https://open-api.weex.com/api/v1/contract/klines`, `/contract/tickers`
- Docstring on every function. Dual logging. py_compile required.

**weex_screener_engine.py** — Reuses signal logic from backtester (shared code):
- Import: `from PROJECTS.four-pillars-backtester.signals.compute_signals import compute_signals`
  (or copy the ATR/stoch/cloud logic — do NOT couple to backtester path; copy what's needed)
- `compute_row(symbol, df)` → dict with: symbol, price, change_24h_pct, atr_ratio, stoch_9, stoch_60, cloud3_bull, signal_now (A/B/C/None), bars_since_signal
- `screen_all(symbols, fetcher, timeframe="5m")` → list of dicts, sorted by atr_ratio desc
- `is_valid(df)` → True if >= 69 bars (minimum for signal validity)
- Returns gracefully on error (empty row, log warning)

**Output interface for Agent 2:**
```python
# screener_engine.py exports:
def screen_all(symbols: list[str], fetcher: WEEXFetcher, timeframe: str = "5m") -> list[dict]:
    # Returns: [{"symbol": "BTC_USDT", "price": 45000, "change_24h_pct": 2.1,
    #            "atr_ratio": 0.0045, "stoch_9": 23, "stoch_60": 18,
    #            "cloud3_bull": True, "signal_now": "A", "bars_since_signal": 0}, ...]
```

---

### Agent 2 — WEEX Screener UI + Telegram alerts
**File:**
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\screener\weex_screener_v1.py`

**Streamlit app:**
- Sidebar: min_atr_ratio (default 0.003), timeframe (5m/15m/1h), signal filter (Any/A/B/None), auto-refresh interval (30s/60s/off)
- Table: symbol | price | 24h% | ATR ratio | stoch_9 | stoch_60 | cloud3 | signal | bars_since
- Color rows: signal_now=A → green, B → yellow, None → neutral
- Auto-refresh: `st.rerun()` with `time.sleep(interval)` — standard Streamlit pattern
- Run command: `streamlit run "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\screener\weex_screener_v1.py"`

**Telegram alerts (key feature):**
- Reuse `Notifier` from `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\notifier.py`
- Load `.env` from bingx-connector root (BINGX_TELEGRAM_TOKEN, BINGX_TELEGRAM_CHAT_ID)
- Alert condition: signal_now in ("A", "B") AND bars_since_signal == 0 (fresh signal only)
- Alert dedup: track `alerted_this_session = set()`. Don't re-alert same symbol+signal within session.
- Message format (HTML):
  ```
  [14:32 UTC+4] <b>WEEX SIGNAL</b>
  <b>Symbol:</b> BTC_USDT
  <b>Grade:</b> A
  <b>ATR ratio:</b> 0.0045
  <b>Stoch 9:</b> 23 | <b>Stoch 60:</b> 18
  <b>Cloud:</b> Bullish
  ```

---

### Agent 3 — Daily P&L Report
**File:**
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\daily_report.py`

**Logic:**
- Read `trades.csv` from bot root (configurable path)
- Filter to today's date (UTC) — column `exit_time` or `entry_time`
- Compute: total_pnl, win_rate, n_trades, n_wins, n_losses, best_trade (symbol + pnl), worst_trade (symbol + pnl)
- Send Telegram via `Notifier` (reuse pattern from notifier.py)
- Message format (HTML):
  ```
  [17:00 UTC+4] <b>DAILY REPORT</b>
  <b>Date:</b> 2026-02-27 | <b>Trades:</b> 12
  <b>P&L:</b> -$47.23 | <b>Win rate:</b> 33%
  <b>Best:</b> RIVER +$31.50
  <b>Worst:</b> GUN -$28.10
  ```
- Run headless (no Streamlit): `python scripts/daily_report.py`
- Task Scheduler setup: run daily at 17:00 UTC (adjust for UTC+4 offset = 21:00 local)
- Provide install command in script docstring

**Task Scheduler command (user runs once):**
```
schtasks /create /tn "BingXDailyReport" /tr "python \"C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\daily_report.py\"" /sc daily /st 21:00
```

---

## Also: Vault update (minor, handled inline)
After build:
- Update `LIVE-SYSTEM-STATUS.md`: BingX Docs Scraper → COMPLETE (16KB markdown reference)
- Update `PRODUCT-BACKLOG.md`: P0.4 → DONE, add screener + daily report as new tasks
- Update `TOPIC-bingx-connector.md`: add screener section

---

## Critical implementation rules (all agents must follow)
- **Docstrings on every def** — one-line minimum
- **py_compile required** — must pass before declaring done
- **Dual logging** — file (`logs/YYYY-MM-DD-screener.log`) + console, timestamps on every line
- **Full Windows paths** in all output and docstrings
- **NO bash execution** — write the files, state the run command, stop
- **NO escaped quotes in f-strings** — use string concatenation for join() expressions
- **Signal logic: copy, don't couple** — do NOT import from backtester path, copy the ATR/stoch math

---

## Parallel execution
All 3 agents launch simultaneously. No dependencies between Agent 2 and Agent 3. Agent 2 depends on the interface defined above for Agent 1 (not the running code — just the dict schema), so it can be written without waiting.

**Post-build verification:**
1. py_compile passes on all 4 files
2. `streamlit run weex_screener_v1.py` launches without error
3. At least one row appears in table within 30s
4. Manually trigger Telegram alert (set a coin as signal=A in test mode)
5. `python daily_report.py` sends Telegram with today's trades (or "no trades today" if empty)
