# Plan: Chronological Log Research — Build Script Orchestrator

**Created:** 2026-03-05
**Purpose:** Build a Python script that orchestrates sequential `claude -p` CLI calls to read all vault logs and write structured findings. Automated, no manual handoffs, single output file.

---

## Context

The vault contains ~201 session logs + ~149 plan files (~87,000 total lines) spanning Jan 2025 to March 2026. Existing files:

- **Prompt:** `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\RESEARCH-TASK-PROMPT.md`
- **Output:** `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\RESEARCH-FINDINGS.md` (empty, ready)

Goal: Build a complete, neutral, factual picture of everything done, decided, changed, and left open. One file at a time, thorough reads, full code verification of referenced scripts.

---

## Architecture

**One Python script** (`scripts/run_log_research.py`) that:

1. Discovers all .md files in `06-CLAUDE-LOGS/` and `06-CLAUDE-LOGS/plans/`
2. Splits them into sized batches
3. For each batch, constructs a prompt and runs `claude -p` via subprocess
4. Waits for completion, logs result, moves to next batch
5. Final batch writes the synthesis

Each `claude -p` invocation gets a **fresh context window** — no 70% limit concerns. The script handles all orchestration.

---

## CLI Invocation Per Batch

```bash
claude -p "<batch_prompt>" \
  --allowedTools "Read,Edit,Glob,Grep" \
  --max-turns 200 \
  --model sonnet \
  --verbose
```

**Key flags:**
- `--allowedTools "Read,Edit,Glob,Grep"` — read-only + append. No Write (prevents overwrites), no Bash.
- `--max-turns 200` — enough for ~25-30 files with code verification (~5-7 turns per file)
- `--model sonnet` — fast, capable enough for research reading. Opus for synthesis only.
- `--verbose` — full turn-by-turn logging to stdout (script captures it)

---

## Batch Design

**Target: ~25 normal files per batch.** Mega-files get dedicated batches.

| Batch | Files | Count | Notes |
|-------|-------|-------|-------|
| 01 | Phase 1: Origins (files 1-11) | 11 | Light warmup |
| 02 | Early Feb (files 12-30) | 19 | Indicator builds, ATR spec, quad rotation |
| 03 | Mid Feb A (files 31-49) | 19 | Backtester, strategy analysis, handoffs |
| 04 | MEGA: 2026-02-13-vault-sweep-review.md | 1 | 14,578 lines — dedicated batch, read in chunks |
| 05 | Mid Feb B (files 51-67) | 17 | BBW layers, 4,361-line vault sweep included |
| 06 | Late Feb A (files 68-85) | 18 | BBW v2, portfolio, trade flow UML |
| 07 | Late Feb B (files 86-100) | 15 | Dashboard, PDF, Python skill, Vince ML |
| 08 | Late Feb C (files 101-120) | 20 | BingX arch, YT analyzer, engine audit |
| 09 | Late Feb D (files 121-142) | 22 | BingX connector, Telegram, VPS, Dash skill |
| 10 | March + Undated (files 143-162) | 20 | Dashboard patches, CUDA, bot sessions |
| 11 | Unlisted files | ~39 | Files in directory but not in original 162 list |
| 12 | Plans — dated (first half) | ~33 | Plans with YYYY-MM-DD prefix |
| 13 | Plans — dated (second half) | ~33 | Remaining dated plans |
| 14 | Plans — auto-generated (first half) | ~42 | Random-named Claude Code plans |
| 15 | Plans — auto-generated (second half) | ~41 | Remaining auto-generated plans |
| 16 | Synthesis | 0 | Read RESEARCH-FINDINGS.md, write synthesis (use opus) |

**Total: 16 batches, ~350 files**

---

## Script Structure

```
C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\run_log_research.py
```

### What the script does:

1. **Discovery phase** — scans `06-CLAUDE-LOGS/` and `06-CLAUDE-LOGS/plans/`, builds ordered file list
2. **Categorization** — separates files into: listed-162 (in prompt order), unlisted, dated-plans, auto-plans
3. **Batch construction** — splits into ~25-file batches, mega-files isolated
4. **Progress file creation** — writes `RESEARCH-PROGRESS.md` with full checkbox list
5. **Sequential execution loop:**
   ```
   for each batch:
     - Build prompt (file list + rules + findings format)
     - Run: subprocess.run(["claude", "-p", prompt, ...])
     - Capture stdout/stderr
     - Log result to console + log file
     - Check RESEARCH-PROGRESS.md for completion
     - If batch failed mid-way, log which files were done and which weren't
     - 10-second pause between batches
   ```
6. **Synthesis batch** — final `claude -p` with `--model opus` reads the full findings and writes synthesis

### Prompt template per batch:

```
You are executing batch {N} of a chronological log research task.

FINDINGS FILE: C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\RESEARCH-FINDINGS.md
PROGRESS FILE: C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\RESEARCH-PROGRESS.md

RULES:
1. Read each file below IN ORDER using the Read tool.
   - For files over 2000 lines, use offset/limit to read ALL chunks. Never skip content.
2. After reading each file, use Edit tool to APPEND findings to the FINDINGS FILE.
3. Use this exact format for each file:
   ---
   ## [filename]
   **Date:** [date]
   **Type:** [Session log / Build session / Strategy spec / Audit / Planning / Other]
   ### What happened
   [Factual summary]
   ### Decisions recorded
   [List or "None."]
   ### State changes
   [What changed]
   ### Open items recorded
   [Pending/unresolved items]
   ### Notes
   [Contradictions with prior logs, or updates to prior decisions]
4. After writing findings, use Edit to update PROGRESS FILE — change "- [ ]" to "- [x]" for that file.
5. CODE VERIFICATION: If a log references a Python script as a key deliverable:
   - Use Glob to find the script
   - Use Read to verify it exists and its content matches the log's claims
   - Note verification result in the findings
6. Be thorough and neutral. Record facts, not interpretation.
7. Do NOT skip any file. Do NOT read two files before writing findings for the first.

FILES TO READ (in order):
{file_list}
```

### Error handling:

- If `claude -p` returns non-zero exit code: log error, pause, ask user (or retry once)
- Script writes its own log to `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\logs\YYYY-MM-DD-research-orchestrator.log`
- If a batch partially completes (some files checked off in PROGRESS, others not): script detects this and builds a retry batch with only the unchecked files

---

## Files Created by This Plan

| File | Purpose |
|------|---------|
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\run_log_research.py` | Build script — the orchestrator |
| `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\RESEARCH-PROGRESS.md` | Created by the script at runtime — full checkbox tracker |
| `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\RESEARCH-FINDINGS.md` | Already exists — appended to by each batch |
| `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\logs\YYYY-MM-DD-research-orchestrator.log` | Runtime log of all batch results |
| `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-05-research-execution-plan.md` | Vault copy of this plan |

---

## Estimated Runtime

- **Batches 1-15** (sonnet, ~25 files each): ~15-30 min per batch = **4-7.5 hours total**
- **Batch 16** (opus, synthesis): ~20-40 min
- **Total: ~5-8 hours unattended**

User runs the script once from terminal and walks away. Script handles everything.

---

## Run Command

```bash
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester"
python scripts/run_log_research.py
```

---

## Verification (After Script Completes)

1. `RESEARCH-PROGRESS.md` — all ~350 checkboxes marked `[x]`
2. `RESEARCH-FINDINGS.md` — one findings section per file + synthesis at the bottom
3. Synthesis answers all 8 questions from the research prompt
4. Orchestrator log shows all 16 batches completed with exit code 0
