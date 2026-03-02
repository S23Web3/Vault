# Plan: BingX Automation — Screener + Daily Report — 2026-02-27

## Context
BingX demo validated. Bot trades but no feedback loop: can't see live signal state across coins, performance review requires manual CSV reads. Build two headless automation tools using existing code patterns. WEEX screener stays in backlog for next week.

---

## What's being built (2 parallel agents)

| File | Purpose |
|------|---------|
| `screener/bingx_screener.py` | Headless loop: fetches klines for all 47 coins, runs signal detection, fires Telegram on fresh A/B signals |
| `scripts/daily_report.py` | Reads trades.csv, computes day P&L + win rate + best/worst, sends Telegram |

---

## Agent 1 — BingX Live Screener (headless, automated)

**File:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\screener\bingx_screener.py`

**Key design decisions:**
- Reuse `FourPillarsV384` plugin directly — already has `get_signal(df)` that calls `compute_signals()` internally
- Reuse `_fetch_klines()` pattern from `data_fetcher.py` exactly (same endpoint, same parsing)
- Live BingX API (`https://open-api.bingx.com`), NOT VST — klines are public, no auth
- Reads coin list from `config.yaml` (same 47 coins as bot)
- Loop every 60s — enough resolution on 5m bars

**Implementation:**

```python
# Imports
import yaml, logging, time, requests, pandas as pd
from pathlib import Path
from datetime import datetime
import sys

# Sys path setup (same pattern as four_pillars_v384.py)
_ROOT = Path(__file__).resolve().parent.parent  # bingx-connector/
_BACKTESTER = _ROOT.parent / "four-pillars-backtester"
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_BACKTESTER))

from plugins.four_pillars_v384 import FourPillarsV384
from notifier import Notifier
```

**Functions:**
- `load_config()` → reads `config.yaml`, returns symbols list + strategy sub-block + telegram config
- `setup_logging()` → dual handler, `logs/YYYY-MM-DD-screener.log`
- `fetch_klines(session, symbol, base_url, timeframe="5m", limit=201)` → DataFrame — copy `_fetch_klines()` logic from `data_fetcher.py`, standalone function (not a class method)
- `compute_atr_ratio(df)` → float: `atr / close` from last closed bar (iloc[-2])
- `run_screener_loop(config, plugin, notifier)`:
  - Loop forever with `time.sleep(60)`
  - For each symbol: fetch → `plugin.get_signal(df)` → if signal and bar_ts is new → Telegram alert
  - Dedup: `last_alerted = {}` dict `{symbol: bar_ts}` — skip if bar_ts unchanged

**Alert dedup logic:**
```python
sig = plugin.get_signal(df)
if sig and last_alerted.get(symbol) != sig.bar_ts:
    last_alerted[symbol] = sig.bar_ts
    send_alert(notifier, symbol, sig, atr_ratio)
```

**Telegram message:**
```
[14:32 UTC+4] <b>BINGX SIGNAL</b>
<b>Symbol:</b> BTC-USDT
<b>Grade:</b> A | <b>Direction:</b> LONG
<b>ATR ratio:</b> 0.0045
<b>Entry:</b> 45000 | <b>SL:</b> 44100 | <b>TP:</b> 46800
```

**Run command:**
```
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\screener\bingx_screener.py"
```

**Logging:** dual handler, `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\logs\YYYY-MM-DD-screener.log`

---

## Agent 2 — Daily P&L Report

**File:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\daily_report.py`

**Logic:**
- Hardcoded path: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\trades.csv`
- Load CSV → filter where `exit_time` (UTC date portion) == today
- If no trades: send "No closed trades today" Telegram message + exit 0
- Compute:
  - `total_pnl` = sum of `pnl` column
  - `n_trades` = count of rows
  - `n_wins` = count where `pnl > 0`
  - `win_rate` = n_wins / n_trades (%)
  - `best_trade` = row with max pnl → (symbol, pnl)
  - `worst_trade` = row with min pnl → (symbol, pnl)
- Load Telegram creds from `.env` (same as bot: `BINGX_TELEGRAM_TOKEN`, `BINGX_TELEGRAM_CHAT_ID`)
- Send via `Notifier` (import from `notifier.py`)

**Telegram message:**
```
[21:00 UTC+4] <b>DAILY REPORT — 2026-02-27</b>
<b>Trades:</b> 12 | <b>Win rate:</b> 33%
<b>P&L:</b> -$47.23
<b>Best:</b> RIVER LONG +$31.50
<b>Worst:</b> GUN SHORT -$28.10
```

**Run headless:** `python scripts/daily_report.py`

**Task Scheduler (user runs once, as admin):**
```
schtasks /create /tn "BingXDailyReport" /tr "python \"C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\daily_report.py\"" /sc daily /st 21:00 /f
```
(21:00 local = 17:00 UTC for UTC+4)

**Logging:** prints to console + `logs/YYYY-MM-DD-daily-report.log`

---

## Critical rules (both agents)
- Docstring on every `def`
- `py_compile` must pass before done
- Dual logging: file (`logs/YYYY-MM-DD-*.log`, created at startup) + StreamHandler
- Full Windows paths in all output
- NO bash execution — write files, state run commands, stop
- NO escaped quotes in f-strings — use string concatenation for `.join()`
- sys.path insert pattern: copy from `four_pillars_v384.py` (lines 14-20)
- Column rename before plugin: `time → timestamp`, `volume → base_vol` (same as plugin does)

---

## Files touched
- NEW: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\screener\bingx_screener.py`
- NEW: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\daily_report.py`
- NO changes to existing files

---

## Verification
1. `py_compile` passes on both files
2. `python bingx_screener.py` starts without error, logs "Screener loop started, N coins"
3. Within 2 minutes: at least one coin row logged (signal or no-signal)
4. `python daily_report.py` sends Telegram with today's trade count (even if 0)
5. Task Scheduler command creates "BingXDailyReport" task (verify in Task Scheduler UI)
