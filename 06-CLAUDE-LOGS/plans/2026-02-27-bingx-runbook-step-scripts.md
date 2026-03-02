# Plan: BingX Bot Runbook — Master Script (Steps 2-11)

**Date**: 2026-02-27
**Session ref**: cozy-swimming-lake.md (runbook), fluffy-singing-mango.md (spec)
**Bot root**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector`

---

## Context

Steps 0-1 done. executor.py has FIX-2 + FIX-3 (backup exists). Steps 2-11 remain.

**Approach**: Single master script `scripts/run_steps.py`. User runs it once. Script shows full permission summary upfront (all files it will modify, create, backup). User approves once. Then all steps run sequentially, unattended, with Ollama streaming visible in terminal. If any step fails (py_compile, Ollama error), script stops immediately and reports which step failed.

---

## What We Build

One file: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\run_steps.py`

Run command:

```
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector"
python scripts/run_steps.py
```

---

## Script Flow

### Phase 1: Permission Request (before ANY action)

Script prints full summary of all files to modify, create, backup, plus Ollama/pytest counts. User types `y` once. No more prompts after that.

### Phase 2: Sequential Execution

For each Ollama step: print banner, read source, stream Ollama, strip fences, py_compile (halt on fail), show diff, backup + replace, log.

For pytest steps (4, 8, 11): run pytest, parse pass count, halt if < 67.

### Phase 3: Summary

Print final report: steps completed, files modified, test results.

---

## Critical Files

| File | Line refs | Modified by |
|------|-----------|-------------|
| `position_monitor.py` | __init__ L20, commission L268, check() L222 | step 2, step 7 |
| `main.py` | PositionMonitor L190-194, set_leverage L196-199, shutdown L244-257 | step 3, step 6 |
| `state_manager.py` | close_position L85, 176 lines total | step 9 |
| `risk_gate.py` | evaluate() L25, 84 lines total | step 9 |
| `executor.py` | already patched (FIX-2+3) | step 9 (101209 only) |
| `ws_listener.py` | does not exist yet | step 5 (new) |
| `scripts/reconcile_pnl.py` | does not exist yet | step 10 (new) |

---

## Verification

- py_compile MUST pass after every Ollama step (script halts on failure)
- pytest runs at steps 4, 8, 11 -- must show >= 67 passing (script halts if not)
- All actions logged to `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-27-bingx-bot-live-improvements.md`
- Final summary printed at end with all results
