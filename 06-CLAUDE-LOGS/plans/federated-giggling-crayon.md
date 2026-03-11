# Handoff Prompt — Strategy Catalogue: Full Inventory + Visualization for Vince

**Date:** 2026-03-07
**Purpose:** Continue the strategy catalogue session. The first session documented 5 strategies. Many more exist. This session completes the full inventory and produces market-reading perspective visualizations for ALL strategies — to feed into Vince ML pipeline design.

---

## WHAT WAS DONE ALREADY (do not repeat)

Session log: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-03-07-strategy-catalogue-visual-plan.md`

5 strategies already visualized:
- S1: Strategy Bible (v3.3 era) — 60-macro + 40-divergence + 9-cycle + 55 EMA
- S2: Four Pillars v3.8.1 — full 4-stoch + Ripster clouds + BBWP
- S3: Four Pillars v3.8.4 (current) — AVWAP phases + BBWP + 4-stoch + Cloud 4 TP
- S4: BingX Bot v1.5 — ATR SL + TTP + EMA filter + BE raise
- S5: 55/89 EMA Cross Scalp (research) — EMA delta + 4-stoch + TDI + BBW

Script already written:
`C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\visualize_strategy_perspectives.py`

---

## STRATEGIES NOT YET VISUALIZED

These exist in the vault and need market-reading perspectives added:

| Strategy | Key Source File |
|----------|----------------|
| Ripster EMA Cloud System | `C:\Users\User\Documents\Obsidian Vault\02-STRATEGY\Indicators\Ripster-EMA-Clouds-Strategy.md` |
| Quad Rotation Stochastic | `C:\Users\User\Documents\Obsidian Vault\02-STRATEGY\Indicators\Quad-Rotation-Stochastic.md` |
| Core Three Pillars Framework | `C:\Users\User\Documents\Obsidian Vault\02-STRATEGY\Core-Trading-Strategy.md` |
| BBWP Volatility Filter | `C:\Users\User\Documents\Obsidian Vault\02-STRATEGY\Indicators\BBWP-v2-BUILD-SPEC.md` |
| ATR SL Movement (3-phase) | `C:\Users\User\Documents\Obsidian Vault\02-STRATEGY\Indicators\ATR-SL-MOVEMENT-BUILD-GUIDANCE.md` |
| AVWAP Confirmation | `C:\Users\User\Documents\Obsidian Vault\02-STRATEGY\Indicators\AVWAP-Anchor-Assistant-BUILD.md` |

---

## WORKING MODE (mandatory)

- Research and document only. No code until user says "build it."
- Do NOT launch explore agents while user is typing.
- Read source files directly. Do not reconstruct from memory.
- Perspectives = WHAT INDICATORS ARE SENSED + WHAT MARKET STATE IS REQUIRED. Not entry/exit mechanics.
- Goal: produce a clear map of every strategy's market-reading logic so Vince ML can learn from all of them.

---

## TASK FOR THIS SESSION

1. Read each source file listed above (one at a time, confirm before moving to next)
2. For each strategy, write a market-reading perspective summary:
   - What indicators does it read?
   - What state must the market be in to qualify?
   - What does "aligned" mean for this strategy?
3. Add these as S6–S11 to the existing visualizer script (or create v2 if cleaner)
4. When user says "build it" — only then write/extend the script

---

## MANDATORY FIRST READS

1. `C:\Users\User\Documents\Obsidian Vault\CLAUDE.md`
2. `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-03-07-strategy-catalogue-visual-plan.md`
3. `C:\Users\User\Documents\Obsidian Vault\09-ARCHIVE\four-pillars-version-history.md`

Then read strategy source files one at a time as you work through the list.

---

## BUILD RULES (if code is written)

- Python skill mandatory before any .py file
- py_compile must pass on every file written
- NEVER overwrite existing files — version bump or new name
- Full Windows paths everywhere
- Log session to: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-03-07-strategy-catalogue-visual-plan.md` (append, Edit tool only)
