# Build Prompt — 55/89 Scalp Signal Bot
**Date:** 2026-03-06
**Purpose:** Next-chat prompt to scope, build, and backtest the 55/89 EMA cross scalp signal

---

## MANDATORY FIRST STEPS

1. Read `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\INDEX.md`
2. Read `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-03-06-uml-55-89-scalp-session.md`
3. Read `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-04-position-management-study.md`
4. Read `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-04-1m-ema-delta-scalp-concept.md`
5. Confirm you understand what was stated by the user vs what was invented by Claude before proceeding

---

## THE SIGNAL — EXACTLY AS STATED BY USER

Three conditions only. No additions. No interpretation.

1. All 4 stochastics align (9 / 14 / 40 / 60)
2. 55/89 EMA cross on 1m chart
3. Move SL to breakeven after cross confirms

**Do not add any conditions, parameters, or logic not listed above.**

---

## WHAT TO BUILD

This is a SIDE BOT — separate from the main Four Pillars bot (v384/v385).

### Scope

**Phase 1 — Signal Backtest**
- Implement the 55/89 scalp signal in the existing backtester framework
- Run across historical 1m data (use existing Bybit/BingX parquet cache)
- Output: signal hit rate, trade count, basic PnL per coin
- Display results in the existing dashboard (v3.9.x) as a new tab or panel

**Phase 2 — Side Bot**
- Build a standalone bot connector for this signal only
- Separate config, separate entry point — does NOT touch the main bot
- Same infrastructure: BingX exchange, Telegram notifications, trades.csv logging

### What to confirm before writing any code

1. Which coins to run the backtest on — ask user
2. SL size — 2x ATR assumed from position management study, confirm with user
3. TP rule — not stated by user, ask before assuming anything
4. Whether Phase 2 (live bot) is in scope for this session or Phase 1 only

---

## RULES FOR THIS BUILD

- Show scope confirmation before writing a single line of code
- Do not invent entry conditions, exit conditions, or parameters
- If something is not stated by the user, ask — do not assume
- Python only, Windows paths, pathlib, pandas
- py_compile check on every file before handing back
- Log session to `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\YYYY-MM-DD-55-89-scalp-build.md`

---

## REFERENCE FILES

- Existing backtester: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\`
- Existing bot connector: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\`
- Parquet data cache: check INDEX.md for current location
- Dashboard: check INDEX.md for current version path
