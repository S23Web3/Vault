# Session 10/2 - Clear Instructions

**Date**: 2026-02-10 (After break)
**Context**: BUILD-JOURNAL-2026-02-10.md in memory folder
**User frustration**: 4 hours wasted on wrong problem

## CRITICAL: What User Actually Needs

**Bulletproof 24/7 execution system** for scalping, NOT just Qwen.

Real requirement:
- Run ANY long-running task 24/7
- Survive crashes, power cuts, reboots
- Auto-restart and resume from checkpoint
- Remote status monitoring
- Zero manual intervention

User's goal: 24/7 scalping - monitor markets continuously

What was delivered: 4 hours trying to get Qwen working (wrong focus)

## Priority 1: Build Executor Framework (MANDATORY - 2 hours max)

Location: `trading-tools/executor/`

Files to create:
- task_runner.py (main entry - runs tasks with health monitoring)
- watchdog.py (process monitor - restarts on crash/hang)
- checkpoint.py (generic checkpoint/resume)
- config.yaml (task definitions)
- dashboard.py (Flask web UI - http://localhost:5000)
- README.md (usage guide)

See BUILD-JOURNAL-2026-02-10.md for full specs.

## Priority 2: Fix Qwen Parser (30 min)

File: `auto_generate_files.py` line 135-184
Problem: Parser looks for "File X.Y:" but Qwen uses "# filename.py"
Solution: Update regex to: r"```python\s*\n#\s*([^\n]+\.py)\s*\n(.*?)```"

## Priority 3: Test Crash Recovery (30 min)

Must pass ALL tests:
- Kill process mid-task → watchdog restarts
- Reboot PC → auto-starts via startup folder
- Power cut → resumes from checkpoint
- Run 30+ minutes unattended → no crashes
- Check dashboard from another device → accessible

## Success Criteria

User should be able to:
1. Start executor with ONE command
2. Leave desk IMMEDIATELY
3. Check status from phone
4. Trust system runs 24+ hours unattended
5. Return to completed work (no crashes)

If ANY criteria fails = session failed

## Time Budget: 2-3 hours MAX

If exceeding 3 hours, you're doing it wrong.

## What User Has When They Return

- Executor framework working
- Tests passing (crash recovery)
- Documentation clear
- ONE command to start
- Zero babysitting required

Get it right this time.
