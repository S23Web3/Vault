# Handoff Prompt — 55/89 EMA Cross Scalp: Continue from Build

**Date:** 2026-03-07
**Purpose:** New chat handoff. The master build script was written and syntax-validated on 2026-03-06. The user has NOT yet run it. This chat continues from that point — run the build, verify outputs, run tests, run standalone backtest.

---

## CONTEXT

The 55/89 EMA Cross Scalp backtest was fully designed and the master build script written in a prior session. No files have been executed yet. This chat picks up from:

- `build_55_89_scalp.py` — written, py_compile PASS, NOT YET RUN
- 4 output files do NOT yet exist on disk

---

## BASH PERMISSIONS NEEDED

Grant ALL of these upfront:

```
Tool: Bash — "py_compile validation on generated .py files"
Tool: Bash — "python -c 'import py_compile; py_compile.compile(...)'"
Tool: Bash — "ls / dir commands to check file existence"
Tool: Read — any file in C:\Users\User\Documents\Obsidian Vault\
Tool: Write — new files only (never overwrite existing without version bump)
Tool: Edit — append to session log, edit existing files
Tool: Glob — file pattern searches
Tool: Grep — code content searches
```

---

## MANDATORY FIRST READS

Read these IN ORDER before doing anything:

1. `C:\Users\User\Documents\Obsidian Vault\CLAUDE.md`
2. `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-03-06-55-89-scalp-backtest-build.md` — what was built, user answers to all 4 open questions, signal architecture, run commands
3. `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\research\55-89-scalp-methodology.md` — complete signal specification (source of truth)

---

## WHAT WAS BUILT (2026-03-06)

### User answers locked in:

| # | Question | Answer |
|---|----------|--------|
| 1 | Initial SL | 2.5x ATR |
| 2 | Exit rule | Trailing stop at 2.5x ATR behind price |
| 3 | BE trigger | EMA cross = entry = immediate BE move |
| 4 | Dashboard approach | New file (keep v394 untouched) |

### Master build script (written, syntax OK, NOT RUN):

`C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_55_89_scalp.py`

### Files it will create when run:

| # | File | Full Path |
|---|------|-----------|
| 1 | Signal module | `C:\...\signals\ema_cross_55_89.py` |
| 2 | Standalone runner | `C:\...\scripts\run_55_89_backtest.py` |
| 3 | Test script | `C:\...\scripts\test_55_89_signals.py` |
| 4 | Dashboard | `C:\...\scripts\dashboard_v394_55_89.py` |

---

## WHAT TO DO IN THIS CHAT

Step 1 — Tell user to run the build script:
```
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_55_89_scalp.py"
```

Step 2 — Read the output. If any file FAILs py_compile, fix the build script and ask user to re-run. Do NOT silently patch output files — fix the source in build_55_89_scalp.py.

Step 3 — Tell user to run tests:
```
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\test_55_89_signals.py"
```

Step 4 — Fix any test failures. Tests check: imports, all required engine columns present, Markov states valid, D lines correct, TDI/BBW states valid, signal counts non-zero.

Step 5 — Tell user to run standalone backtest:
```
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\run_55_89_backtest.py" --symbol BTCUSDT
```

Step 6 — Read results. Report: total trades, WR, R:R, net PnL. Compare against Four Pillars v3.8.4 baseline.

Step 7 — If all passes: user may optionally launch dashboard:
```
streamlit run "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_v394_55_89.py"
```

---

## KNOWN CAVEAT

The Backtester384 engine uses AVWAP-based trailing by default, not ATR trailing. `sl_mult=2.5` sets initial SL at 2.5x ATR. The engine's AVWAP ratchet provides trailing behavior. True ATR trailing would require engine modification — flagged for future work, NOT in scope for this session.

---

## BUILD RULES (mandatory)

- Read `CLAUDE.md` first — all hard rules apply
- NEVER overwrite existing files — check existence first
- NEVER use escaped quotes in f-strings inside build scripts
- ALL functions must have docstrings
- Full Windows paths everywhere
- Log session to: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-03-07-55-89-scalp-run-and-test.md`
- Do NOT execute Python scripts via Bash — give user the run command, wait for output

---

## REFERENCE FILES

| File | What |
|------|------|
| `C:\...\06-CLAUDE-LOGS\2026-03-06-55-89-scalp-backtest-build.md` | Build session log — all decisions, architecture, validation |
| `C:\...\research\55-89-scalp-methodology.md` | Signal spec source of truth |
| `C:\...\signals\stochastics_v2.py` | Raw K stoch (JIT) — reused by signal module |
| `C:\...\signals\clouds_v2.py` | EMA function (JIT) — reused by signal module |
| `C:\...\engine\backtester_v384.py` | Engine the dashboard uses |
| `C:\...\scripts\build_55_89_scalp.py` | Master build script (READ THIS before anything else) |
