# Session Log: Research Orchestrator Build
**Date:** 2026-03-05
**Topic:** Automated chronological log research via Claude Code CLI batches

---

## What was built

`C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\run_log_research.py`

Python orchestrator that runs sequential `claude -p` CLI calls to read all ~350 vault logs and plan files, writing structured findings per batch. Designed for unattended overnight execution.

---

## Architecture

- **Discovery:** Scans `06-CLAUDE-LOGS/` + `06-CLAUDE-LOGS/plans/`, categorizes into: 160 ordered (from RESEARCH-TASK-PROMPT.md list), 39 unlisted, 69 dated plans, 85 auto-generated plans
- **Batching:** 20 files per batch, mega files (>5000 lines) isolated into dedicated batches. 21 file batches + 1 synthesis = 22 total
- **Execution:** `type prompt_file.txt | claude.cmd -p --allowedTools ... --model sonnet` (shell=True, cmd.exe native pipe)
- **Synthesis:** Final batch uses opus model, reads all FINDINGS-*.md, writes SYNTHESIS.md
- **Merge:** All batch files merged into RESEARCH-FINDINGS.md

## Key config

| Setting | Value |
|---------|-------|
| BATCH_SIZE | 20 files |
| BATCH_PAUSE_SECONDS | 1500 (25 min) |
| MAX_RETRIES | 2 |
| RETRY_BACKOFF_SECONDS | 900 (15 min) |
| RATE_LIMIT_BACKOFF_SECONDS | 1800 (30 min) |
| BATCH_TIMEOUT_SECONDS | 7200 (2h) |
| MAX_TURNS_NORMAL | 150 |
| MAX_TURNS_MEGA | 80 |
| MAX_TURNS_SYNTHESIS | 100 |
| RESEARCH_MODEL | sonnet |
| SYNTHESIS_MODEL | opus |

## Bugs fixed during build

1. `return False` → `return False, False` in except handler (tuple unpack crash)
2. Duplicate "RESEARCH-FINDINGS.md" in EXCLUDE_FILES
3. `subprocess.run(["claude", ...])` — bare `claude` not in PATH → hardcoded `CLAUDE_CMD` full path
4. `shell=False` cannot execute `.cmd` batch files on Windows → `shell=True`
5. Python stdin pipe through cmd.exe→claude.cmd not forwarding → temp file + `type file | claude` approach
6. Duplicate log output → `logger.propagate = False`

## Output files (created at runtime)

| File | Purpose |
|------|---------|
| `06-CLAUDE-LOGS/RESEARCH-PROGRESS.md` | Checkbox tracker (353 files) |
| `06-CLAUDE-LOGS/research-batches/FINDINGS-*.md` | Per-batch findings |
| `06-CLAUDE-LOGS/research-batches/SYNTHESIS.md` | Final synthesis |
| `06-CLAUDE-LOGS/RESEARCH-FINDINGS.md` | Merged output |
| `06-CLAUDE-LOGS/logs/2026-03-05-research-orchestrator.log` | Runtime log |

## Run status

- Batch 1 (ordered-01, 20 files): COMPLETE at 19:49:40. 20/20 files checked off.
- Covers: 2025-01-21 to 2026-02-03
- Pausing 1500s before batch 2

## Run command

```bash
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester"
python scripts/run_log_research.py
```

## Resume after interruption

Script skips batches where FINDINGS-*.md exists AND all files are checked off in RESEARCH-PROGRESS.md. Re-run the same command to resume.

Before re-running from scratch: delete `RESEARCH-PROGRESS.md` and all `research-batches/` files.
