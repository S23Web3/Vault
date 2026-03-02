# Session: Trade Analysis Script + BE+Fees Fix
**Date**: 2026-02-28
**Project**: BingX Connector

---

## Work Done

### 1. analyze_trades.py — Completed
Script at `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\analyze_trades.py`.

Phase 3 only ($50 notional, 5m live). Fetches live mark prices (public API) and actual open orders from BingX auth API (SL, trailing TP) to compute 3-scenario True Total P&L.

Run: `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\analyze_trades.py"`
Report output: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-28-bingx-trade-analysis.md`

Key constants:
- `COMMISSION_TAKER = 0.0005` (0.05% per side, BingX)
- `COMMISSION_RT_GROSS = 0.001`
- `COMMISSION_REBATE = 0.50`
- `BE_TOLERANCE = 0.0005`
- `MARGIN_USD = 5.0`, `LEVERAGE = 10`, `notional = $50`

### 2. BE+Fees Analysis Fix — analyze_trades.py

**Problem**: `identify_be_trades` labeled exits at exact entry as "break-even" — they are NOT. Each costs exit commission (~$0.025 net).

**Fix**:
- Renamed `identify_be_trades` → `identify_sl_at_entry_trades`
- Section 3 renamed "Break-Even Trade Analysis" → "SL-at-Entry Exit Analysis"
- Blockquote now says: "Bot raises SL to exact entry (NOT entry + fees)"
- Table row: "SL-at-entry exits (NOT true BE — see note)"
- Key Findings updated to explain cost per trade

### 3. BE+Fees Explanation (user asked to explain better)

| Scenario | Net P&L per trade |
|----------|------------------|
| Current (SL at entry) | -$0.025 net (pay exit commission) |
| True BE+fees (SL at entry + 0.10%) | $0.00 net gross / +$0.025 after rebate |

17 SL-at-entry exits in Phase 3 = -$0.425 avoidable commission loss.
True BE+fees = SL at `entry * 1.001` for LONG, `entry * 0.999` for SHORT.

### 4. Bot Fix — main.py

**File**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main.py` line 127

Changed fallback commission rate: `0.0016` → `0.001`

Old: `return 0.0016  # fallback: 0.08% x 2 sides`
New: `return 0.001  # fallback: 0.05% x 2 sides (BingX taker rate)`

The bot already fetches the real rate from BingX API at startup; this only affects the fallback if the API call fails.

### 5. Bot Fix — position_monitor.py (logging)

**File**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\position_monitor.py`

`_place_be_sl()`: added `notional` + `commission_usd` variables.
Log line now shows: rate%, commission covered in USD, order ID.

`check_breakeven()`: Telegram renamed `BE+FEES RAISED` (was `BREAKEVEN RAISED`).
Message now shows: `SL -> be_price  (+0.100% covers $0.05 RT commission)`.
Logger: `BE+fees raised: ... (+0.1000%) covers=$0.05 RT commission`

**Note**: `_place_be_sl()` was ALREADY correct — it places at `entry * (1 + commission_rate)`. The fixes are to the fallback rate and the logging clarity.

### 6. py_compile Results
All files syntax OK:
- `scripts/analyze_trades.py` — OK
- `main.py` — OK
- `position_monitor.py` — OK

---

## Q-USDT Clarification
User questioned Q-USDT showing -$1.36 in worst symbols. Confirmed: 2 separate trades, both SL hits:
- LONG: entry 0.023621, exit 0.023269, SL dist 1.49%, P&L -$0.77
- SHORT: entry 0.023023, exit 0.023278, SL dist 1.11%, P&L -$0.59
Symbol leaderboard aggregates by symbol. Neither individual loss is anomalous.

---

## Files Changed This Session

| File | Change |
|------|--------|
| `scripts/analyze_trades.py` | `identify_be_trades` → `identify_sl_at_entry_trades`, Section 3 relabeled |
| `main.py` | Fallback commission rate 0.0016 → 0.001 |
| `position_monitor.py` | BE logging: Telegram renamed BE+FEES, commission USD shown |
