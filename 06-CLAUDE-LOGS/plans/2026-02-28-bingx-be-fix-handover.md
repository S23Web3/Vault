# BingX BE Fix — Handover Prompt for Next Session
**Date:** 2026-02-28
**Use:** Paste this as the opening message of the next chat session.

---

CONTEXT
-------
BingX live bot ($5 margin, 10x leverage = $50 notional per trade).
Live account: $110. Running on real money.

The previous session fixed trailing take profit (Approach C implemented in executor.py).
THIS session is about breakeven only. No TTP work, no SL work.

PERSPECTIVE ON TRADE SIZE
--------------------------
This is a very small account. $5 margin × 10x = $50 notional per trade.
At 0.08% taker fee: commission per side = $0.04. Round-trip = $0.08.
Slippage on a $50 STOP_MARKET fill: likely $0.01–0.05.
Total dollar exposure of the BE problem: pennies per trade.

This does NOT mean the problem is unimportant — it means the fix should be
pragmatic and proportionate. The goal is correctness (does BE actually
break even?) not perfection. A solution that costs 3 API calls to save $0.05
is worse than a simple fix that gets the stop price right.

PROBLEM STATEMENT
-----------------
Breakeven raise code fires (confirmed in logs: ELSA, VIRTUAL on demo).
But the resulting trades appear to still exit at a loss.

User's primary doubt: the stop is placed as a STOP_MARKET (executes at
whatever market price it gets), not a limit-type order. On a fast-moving
small-cap coin, slippage on a STOP_MARKET fill could eat the gain.

Secondary doubt: the stop may be placed at the wrong price — at raw
entry_price instead of entry_price + commission round-trip (the true
zero-loss exit level).

Note: BE "confirmed working" means the raise logic FIRED and PLACED the order
on VST demo. It does NOT confirm the resulting exit was profitable. VST has
known price corruption (STOP orders fill at wrong prices). On live, it is
not yet confirmed whether:
  (a) BE raise is even firing at all, or
  (b) BE raise fires but exit price is wrong.
Check the live logs first before assuming which problem exists.

SCOPE — BE ONLY
---------------
- Focus: _place_be_sl(), check_breakeven(), BE_TRIGGER constant
- Out of scope: SL logic, trailing TP, new entries, risk gate

WHAT TO INVESTIGATE
-------------------
1. Read position_monitor.py in full.
   Path: C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\position_monitor.py

2. Find the current _place_be_sl() implementation:
   - What order type is used? (STOP_MARKET? STOP_LIMIT?)
   - What stopPrice is passed? (entry_price exactly? or entry + commission?)
   - What is BE_TRIGGER (currently 1.0016)?

3. Verify the math:
   - Commission RT = 0.0008 × 2 = 0.0016 (0.16%)
   - True BE exit price for LONG = entry × (1 + 0.0016) / (1 - 0.0008) ≈ entry × 1.0024
     (commission is paid on both entry AND exit notional)
   - Current stop at entry_price = guaranteed loss of ~0.16% + slippage
   - With $50 notional: 0.16% = $0.08, STOP_MARKET slippage could be another $0.01–0.05
   - BUT: total dollar loss = ~$0.10–0.13 per BE exit. Proportionate fix needed.

4. Check BingX API order type distinction:
   - STOP_MARKET: triggers at stop price, executes as market (slippage risk)
   - STOP_LIMIT: triggers at stop, limit fills at specified price (non-fill risk)
   - For a position pulling back to BE level, STOP_MARKET is probably correct type —
     the real issue is the stop PRICE, not the order type.

5. Read trades.csv (live phase only = last 47 trades, notional ~50.0)
   Path: C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\trades.csv
   Look for: any trades with pnl_net near zero or slightly negative — these are BE exits.
   Check: what exit_reason do they have? What pnl_net?

6. Read live bot logs if available:
   Path: C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\logs\
   Look for: "BREAKEVEN RAISED" Telegram messages and subsequent exit prices.

7. Read the TOPIC file for full BE architecture context:
   C:\Users\User\.claude\projects\c--Users-User-Documents-Obsidian-Vault\memory\TOPIC-bingx-connector.md
   Look at: "Breakeven Raise" section, "BE_TRIGGER = 1.0016" constant.

8. Read the TTP session log (context only, do not redo TTP work):
   C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-28-bingx-ttp-research.md

DELIVERABLE FORMAT
------------------
0. Read above + think about all permissions — user will be AFK.

1. Show current BE implementation as a table:
   | Component        | Current Value | Issue |
   For: trigger price, stop price formula, order type, working type

2. Show the true BE math:
   - What exit price gives PnL = 0 exactly? (show formula)
   - Example with P = 0.08418 (ELSA entry, from confirmed log)
   - Dollar amounts at $50 notional: what does each cent of error cost?
   - Keep it proportionate — $0.08 error on $50 is not a crisis

3. List all approaches to fix it:
   - Approach A: Fix the stop price only — change stopPrice from entry_price
     to entry × (1 + commission_RT). Keep STOP_MARKET. ~2 lines.
   - Approach B: Add slippage buffer — stopPrice = entry × (1 + commission_RT + slippage).
     e.g., entry × 1.003. Adds a small fixed buffer. ~2 lines.
   - Approach C: Change order type from STOP_MARKET to STOP_LIMIT.
     Guarantees fill price but risks non-fill on gaps.
   - Approach D: Replace BE stop with TAKE_PROFIT_MARKET at entry × 1.002.
     Fires when price rises TO the BE level (protects against downward reversal
     via the existing SL, and takes a small profit on upward moves). Different
     semantics — investigate carefully.
   Add any other approaches visible in the code.

4. Comparison table across all approaches:
   | | A | B | C | D |
   Dimensions: stop price, order type, slippage protection, non-fill risk,
   lines of code, dollar impact on $50 notional, recommended?

5. Recommend one approach and implement it.
   Keep it proportionate to the trade size — simpler is better here.
   Files to change: position_monitor.py, tests/test_position_monitor.py (if exists)
   py_compile must pass on all changed .py files.

6. Write session log to:
   C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-28-bingx-be-fix.md
   Update INDEX.md BingX Connector section.

KEY CONSTRAINTS (from MEMORY.md)
---------------------------------
- NEVER execute Python scripts. Write the code, give the run command, stop.
- py_compile MUST pass on every .py file written.
- FULL PATHS everywhere in all output.
- No emojis.
- JOURNALS: Edit tool only (append), never Write.
- SCOPE: BE only. Do not touch TTP, SL gate, risk gate, or entry logic.
- After writing code: run command is:
  cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector"
  python -m pytest tests/ -v
