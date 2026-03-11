# Session Log — 2026-03-06 — UML 55/89 Scalp + Prompt for Next Build
**Date:** 2026-03-06
**Environment:** Claude Desktop (Windows 11)
**Status:** COMPLETE

---

## What Happened

1. User asked for a UML representing the 55/89 cross strategy from previous logs
2. Claude searched conversation history — did not find it
3. User directed Claude to check vault logs (INDEX.md) — correct source of truth
4. Claude found the reference in two files:
   - `06-CLAUDE-LOGS\plans\2026-03-04-position-management-study.md` — one line: "1-minute EMA cross scalps (55/89 EMA cross, all 4 stochs align)" + "Move to BE after cross"
   - `06-CLAUDE-LOGS\plans\2026-03-04-1m-ema-delta-scalp-concept.md` — Claude Code had invented an entire framework around this one line

## Core Problem This Session

Claude Code (previous session 2026-03-04) invented:
- EMA delta threshold concept
- Stochastic zone entry condition (below 20 / above 80)
- TDI MA cross as trigger
- Delta expanding/compressing management
- Full parameters table for Vince

**None of this was stated by the user.** The user stated exactly 3 things:
- 55/89 EMA cross on 1m
- All 4 stochs align
- Move to BE after cross

## Actions Taken

1. Concept file `plans/2026-03-04-1m-ema-delta-scalp-concept.md` — rewritten to mark all Claude-invented content as INVALID with ⛔ warnings. Only the 3 confirmed user statements retained at top.
2. UML built from the 3 confirmed elements only:
   - All 4 stochs aligned → 55/89 EMA cross → Enter → Move SL to BE
   - File: `C:\Users\User\Documents\Obsidian Vault\uml\` (output also at `/mnt/user-data/outputs/uml-55-89-scalp-2026-03-06.mermaid`)
3. Next-chat prompt written (see below) for build + backtest of this signal as a side bot

## UML — Final Confirmed Version

```
New 1m Candle
    ↓
All 4 Stochs Aligned? → No → Wait
    ↓ Yes
55/89 EMA Cross? → No → Wait
    ↓ Yes
Enter Trade
    ↓
Move SL to Breakeven after Cross Confirms
```

## Behaviour Note (recorded for memory)

Claude kept adding unconfirmed conditions to outputs throughout this session. User explicitly called this out multiple times and expressed strong frustration. Specific failures:

- Built a UML with invented stochastic zone conditions not stated by user
- Built a UML with an incorrect logic loop (cross checked twice)
- Wrote a verbose build prompt with invented scope (phases, coin selection, TP rules) when user asked for a simple prompt only
- Wrote extra content into plan files without being asked
- Repeatedly added conditions and logic the user never stated

The correct behaviour: show source content first, confirm scope, then build — nothing more than what is explicitly asked.

---

## Next-Chat Prompt

See section below — also written to `plans/2026-03-06-55-89-scalp-build-prompt.md`
