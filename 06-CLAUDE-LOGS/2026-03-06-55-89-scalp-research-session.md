# Session Log — 2026-03-06 — 55/89 Scalp Research + Master Build Prompt
**Date:** 2026-03-06
**Environment:** Claude Code (VSCode, Windows 11, Opus 4.6)
**Status:** COMPLETE
**Prior session same day:** `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-03-06-uml-55-89-scalp-session.md` (Claude Desktop)

---

## What Happened

This session continued from the UML session (Claude Desktop) and ran across two Claude Code context windows.

### Context Window 1 — Research Methodology + Plan

1. User asked to build a backtest idea for the 55/89 EMA cross scalp signal with 3 elements, run "as if live" (candle-by-candle replay, no lookahead)
2. Read session log + position management study as directed
3. Multiple rounds of correction on what "aligned" means:
   - First attempt: "all 4 K cross above D" -- WRONG. User said no.
   - Second attempt: "at least 2 stochs moving" -- WRONG. User corrected: it's about the overall group character, fast stochs leading, slow catching up.
   - Final: directional momentum building as a group. Fast stochs (9, 14) already moving; slow stochs (40, 60) showing improving degree of change.
4. User clarified: both 55 and 89 are EMAs (not SMA). Markov/B-S are literal builds, not conceptual.
5. User chose: research all three aspects (Markov, OU, scoring), any liquid 1m data, report doc first then Jupyter notebook.
6. Explored backtester codebase — found existing signals (stochastics_v2.py, clouds_v2.py), 371 parquets, research dir.
7. Wrote plan v1. User activated Opus and asked for discrepancy audit.
8. Found 12 discrepancies in v1 (89 labelled SMA, Markov states too rigid, K/D cross as prerequisite, EMA delta separated, missing D lines, no SL/exit rules, OU mean-reversion assumed, independence assumed).
9. Rewrote plan as v2. Wrote full methodology document (8 sections).
10. User added: BBW value (section 6), Monte Carlo full joint sim (section 5), Vince state output (section 6).
11. User confirmed TDI and stoch 9 alert role apply to 55/89 scalp. Added as sections 4 and 5.
12. User clarified stoch 9 K/D cross is THE GATE — not one of four equal stochs. Rewrote section 5 and UML.
13. User asked about running this as a backtest in the dashboard without changing the existing strategy version.

### Context Window 2 (this session) — Master Build Prompt

14. Continued from context summary. User wanted a handoff prompt for a new chat.
15. Wrote initial handoff prompt (BaseStrategy class approach). User rejected: "i want as much as possible a master script that executes the needed, i want all permissions listed as a bash and core focus in it"
16. Explored dashboard architecture (two parallel agents):
    - **Finding:** Dashboard does NOT use BaseStrategy classes. It hardcodes `compute_signals_v383()` + `Backtester384()` directly.
    - **Finding:** Engine expects specific columns: `long_a`, `short_a`, `long_b`, `short_b`, `reentry_long`, `reentry_short`, `cloud3_allows_long/short`, plus OHLCV+ATR.
    - **Finding:** Integration path = create `compute_signals_55_89()` function (same pattern as `compute_signals_v383`), add strategy selector dropdown in sidebar.
17. Rewrote handoff prompt as master-script-focused build prompt with:
    - All bash/tool permissions listed upfront
    - Master script creates 4 files (signal module, dashboard patch, standalone runner, test script)
    - `write_and_validate()` scaffold with py_compile + existence checks
    - Engine column mapping (how 55/89 signals map to long_a/short_a etc.)
    - All reference files with full paths and dashboard line numbers
18. User approved plan. Saved vault copy.

---

## Files Created

| File | What |
|------|------|
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\research\55-89-scalp-methodology.md` | Complete research methodology (8 sections: Markov, OU, slope, TDI, stoch 9 gate, BBW, MC, Vince state) |
| `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-06-55-89-scalp-research-plan.md` | Research plan v2 (corrected after 12-discrepancy audit) |
| `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-06-55-89-scalp-master-build-prompt.md` | Master build prompt for new chat (master script approach, all permissions, architecture findings) |

## Files Read (key ones)

- `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-03-06-uml-55-89-scalp-session.md`
- `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-04-position-management-study.md`
- `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-04-1m-ema-delta-scalp-concept.md`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\strategies\base_strategy.py`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\engine\backtester_v391.py`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\stochastics_v2.py`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\clouds_v2.py`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_v394.py` (via agents)
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\DASHBOARD-FILES.md`

---

## Key Decisions

1. **Stoch 9 is the gate** — system IDLE until it fires. Not one of four equal stochs.
2. **Dashboard uses Backtester384 + compute_signals_v383** — not BaseStrategy classes. New strategy must follow same `compute_signals_*()` function pattern.
3. **Master script approach** — single `build_55_89_scalp.py` creates all files, validates each with py_compile.
4. **No modification to existing code** — new signal module plugs in alongside, dashboard patched or copied.

## Open Questions (for next session)

1. Initial SL value
2. Exit rule (what closes trade after SL at BE)
3. Which cross triggers BE move
4. Dashboard approach: patch v394 or create copy

---

## Next Step

Copy `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-06-55-89-scalp-master-build-prompt.md` as the first message in a new chat. That prompt contains everything needed.
