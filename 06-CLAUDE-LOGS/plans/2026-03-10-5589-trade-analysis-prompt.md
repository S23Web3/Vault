# 55/89 Trade Analysis + Flaw Identification — Agent Prompt

**Date:** 2026-03-10
**For:** New Claude Code session

---

## Prompt

```
# 55/89 EMA Cross Scalp v2 — Trade Analysis + Flaw Identification

## Mandatory first steps (do in this order, no agents)
1. Read C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\PROJECT-STATUS.md
2. Read C:\Users\User\.claude\projects\c--Users-User-Documents-Obsidian-Vault\memory\TOPIC-55-89-scalp.md
3. Read C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-10-5589-v2-redesign-plan.md
4. Read C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\ema_cross_55_89_v2.py
5. Read C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\engine\backtester_55_89.py

Then load the Python skill: /python

---

## Context

The 55/89 EMA Cross Scalp strategy (v2) was redesigned in the last session.
The signal pipeline was rebuilt from scratch:
- Entry: 2-state stoch 9 D overzone (D < 20 for long, D > 80 for short) then exit overzone
- Alignment is a grade system (A/B/C) not an entry gate
- EMA 55/89 cross sets BE after entry (not the entry trigger)
- Regression channel gate at state 2 exit (signals/regression_channel.py)
- TDI uses RSI 14
- Position management: 4-phase AVWAP SL + Phase 4 TP at Cloud 4

A portfolio backtest was run on 10 coins (2025-04-09 date range).
Results PDF: C:\Users\User\Downloads\55_89_portfolio_2025-04-09.pdf

---

## Task 1: Read the PDF

Use pymupdf to extract the PDF:

python -c "
import pymupdf, os
doc = pymupdf.open(r'C:\Users\User\Downloads\55_89_portfolio_2025-04-09.pdf')
for i in range(len(doc)):
    pix = doc[i].get_pixmap(dpi=200)
    out = os.path.join(r'C:\Users\User\Downloads', 'pf_page_' + str(i+1) + '.png')
    pix.save(out)
    print('Saved page', i+1)
"

Then use the Read tool to view each PNG page.

---

## Task 2: Pull the raw trade data

The backtest engine outputs a trades_df with these columns:
  direction, entry_bar, exit_bar, entry_price, exit_price, pnl, commission,
  exit_reason, bars_held, ratchet_count, phase_at_exit, saw_green,
  ema_be_triggered, trade_grade

The parquet data lives in:
  C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\data\historical\
  or data\cache\

To extract the actual trade records for analysis, write a script:
  scripts\run_trade_analysis_5589.py

This script:
1. Loads parquet for each coin in the portfolio (or a single representative coin)
2. Runs compute_signals_55_89 (v2) + Backtester5589 with default params
3. Saves trades_df to results\trades_5589_SYMBOL.csv for each coin
4. Does NOT run via Bash -- outputs run command at end

---

## Task 3: Visualise at least 20 trades

Build a trade visualisation script:
  scripts\visualise_5589_trades.py

For each trade (minimum 20, up to 50), render a matplotlib subplot showing:
- Price bars (OHLC as line or simplified bar) from 10 bars before entry to exit + 5 bars after
- Entry point marked (green triangle up for long, red triangle down for short)
- Exit point marked (circle, colour = green if win, red if loss)
- SL level at entry (horizontal dashed line)
- EMA 55 line
- EMA 89 line
- Stoch 9 D value at entry (text annotation)
- Trade grade at entry (text annotation: A/B/C)
- Exit reason (text annotation: sl_phase1/2/3, tp_phase4, eod)
- PnL in $ (text annotation)
- Whether EMA BE was triggered (annotation if True)

Output: one PNG per coin (20-trade grid, 4 rows x 5 cols) saved to:
  results\trade_viz_5589_SYMBOL.png

---

## Task 4: Plain English trade outline

After reading the trades and visualisations, write a plain English description of:

1. What a typical LONG trade looks like step by step:
   - What was stoch 9 D doing before entry?
   - What triggered the entry?
   - Where was the initial SL placed?
   - What happened to SL over the trade life?
   - When (if ever) did the EMA cross fire and move SL to BE?
   - How did the trade typically exit?

2. What a typical SHORT trade looks like (same structure)

3. Grade breakdown:
   - What % of trades were A/B/C?
   - Did grade correlate with win rate?
   - Did grade A trades win more than C trades?

---

## Task 5: Flaw identification

Based on the trade data and visualisations, identify the core flaws:

For each flaw found, state:
- WHAT: what is happening mechanically
- WHY: why it causes losses
- HOW COMMON: % of trades affected
- FIX: specific code change needed (file + line)

Focus areas:
1. Are trades entering too early (stoch 9 D just barely touched 20 and bounced)?
2. Are trades entering too late (stoch 9 D has already bounced far above 20 by entry bar)?
3. Does the SL in Phase 1 (2.5x ATR) make sense given AXS/altcoin volatility?
4. Is the AVWAP freeze in Phase 2 (5 bars) too tight or too loose for 1m data?
5. Is the EMA 55/89 cross happening BEFORE entry (so BE fires immediately or never)?
6. Is the TP (Phase 4, ratchet >= 2) ever reaching? What % of trades hit Phase 3+?
7. Does trade grade predict outcomes? If C trades are 80% of entries and mostly losses, the cascading alignment concept isn't helping.

---

## Key files

```
PROJECTS/four-pillars-backtester/
  signals/
    ema_cross_55_89_v2.py      Signal pipeline v2 (2-state overzone entry)
    regression_channel.py      Channel gate (orderly decline filter)
    stochastics_v2.py          Raw K stochastics
    clouds_v2.py               EMA computation
  engine/
    backtester_55_89.py        4-phase AVWAP engine + BE trigger
    avwap.py                   AVWAP tracker
  scripts/
    dashboard_55_89_v3.py      Streamlit dashboard
    test_55_89_signals_v2.py   Signal tests (all 7 pass)
    build_5589_v2_redesign.py  Build script (last session)
  data/
    historical/ or cache/      Parquet files per coin
```

## Hard rules (from MEMORY.md)
- Load /python skill before writing any .py file
- py_compile + ast.parse on every file written
- No bash execution of Python -- give commands, user runs
- No emojis anywhere
- Full Windows paths in all output
- Every def must have a docstring

## Output
Deliver:
1. Analysis findings (plain text, no code)
2. Trade visualisation script (full file, ready to run)
3. Run command for the visualisation script
4. Numbered list of flaws with WHAT/WHY/HOW COMMON/FIX for each
```
