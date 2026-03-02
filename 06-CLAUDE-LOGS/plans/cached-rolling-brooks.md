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
Script prints:
```
=== BingX Bot Runbook: Steps 2-11 ===

FILES TO MODIFY (backups created automatically):
  position_monitor.py  (step 2: commission rate, step 7: fill_queue)
  main.py              (step 3: commission fetch, step 6: WS thread)
  state_manager.py     (step 9: cooldown + session_blocked)
  risk_gate.py         (step 9: cooldown check)
  executor.py          (step 9: error 101209 handler)

NEW FILES TO CREATE:
  ws_listener.py           (step 5: WebSocket fill listener)
  scripts/reconcile_pnl.py (step 10: PnL audit tool)

BACKUPS CREATED:
  position_monitor.step02.bak.py
  position_monitor.step07.bak.py
  main.step03.bak.py
  main.step06.bak.py
  state_manager.step09.bak.py
  risk_gate.step09.bak.py
  executor.step09.bak.py

OLLAMA CALLS: 9 (steps 2,3,5,6,7,9x3,10)
PYTEST RUNS: 3 (steps 4,8,11)

Proceed? (y/n):
```

User types `y` once. No more prompts after that.

### Phase 2: Sequential Execution
For each Ollama step:
1. Print step banner (`=== STEP N: description ===`)
2. Read source file, show line count
3. Stream Ollama output (tokens appear live in terminal)
4. Strip markdown fences
5. py_compile — if FAIL: stop immediately, report
6. Show abbreviated diff (first 80 changed lines)
7. Backup original, replace with new
8. Append to session log with timestamp

For pytest steps (4, 8, 11):
1. Run `python -m pytest tests/ -v`
2. Parse output for pass count
3. If < 67 passed: stop immediately, report
4. Log result

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

## Shared Helpers (defined once in master script)

- `stream_ollama(prompt, output_path, model)` — stream:true, tokens to stdout, strip fences, write file
- `py_compile_check(path)` — returns True/False, prints PASS/FAIL
- `show_diff(old_path, new_path)` — git diff --no-index, truncated
- `append_log(msg)` — timestamped append to session log
- `backup_and_replace(source, new_file, step_num)` — copy source to .stepNN.bak.py, copy new over source
- `run_pytest()` — subprocess pytest, parse pass count, return count

---

## Step Prompts (embedded in master script)

Each Ollama step has a prompt string built at runtime by reading the current source file and prepending the spec instructions. Prompts come from fluffy-singing-mango.md specs:

| Step | Target file | Prompt summary |
|------|-------------|---------------|
| 2 | position_monitor.py | Add commission_rate param to __init__, replace hardcoded 0.0012 |
| 3 | main.py | Add COMMISSION_RATE_PATH, fetch_commission_rate(), pass to PositionMonitor |
| 5 | (new) ws_listener.py | Full WSListener class from spec (threading, websockets, listenKey lifecycle) |
| 6 | main.py | Import WSListener, create fill_queue, start/stop ws_thread |
| 7 | position_monitor.py | Add fill_queue param, drain block in check(), _handle_close_with_price() |
| 9a | state_manager.py | Add last_exit_time dict, session_blocked set, block_symbol(), is_blocked() |
| 9b | risk_gate.py | Add cooldown check + session_blocked check to evaluate() |
| 9c | executor.py | Detect 101209, retry halved qty, add to session_blocked |
| 10 | (new) reconcile_pnl.py | Full standalone script: reads trades.csv, calls positionHistory API, logs discrepancies |

---

## Verification

- py_compile MUST pass after every Ollama step (script halts on failure)
- pytest runs at steps 4, 8, 11 — must show >= 67 passing (script halts if not)
- All actions logged to `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-27-bingx-bot-live-improvements.md`
- Final summary printed at end with all results
