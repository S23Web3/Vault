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
  --allowedTools "Read,Edit,Write,Glob,Grep" \
  --max-turns 200 \
  --model sonnet
```

**Key flags:**
- `--allowedTools "Read,Edit,Write,Glob,Grep"` — pre-approves all tools. Zero interactive prompts.
- `--max-turns 200` — enough for ~25 files with code verification (~5-7 turns per file)
- `--model sonnet` — fast, capable enough for research reading. Opus for synthesis only.

---

## Batch Design

**Target: ~25 normal files per batch.** Mega-files (>5000 lines) get dedicated batches.

Batches are built dynamically by the script:
- Ordered files (162 from RESEARCH-TASK-PROMPT.md) go first, in exact order
- Unlisted files (found on disk but not in the 162 list) go next
- Dated plan files follow
- Auto-generated plan files last
- Synthesis is the final batch

Each batch writes to its own file: `research-batches/FINDINGS-<batch-name>.md`
Script merges all batch files into `RESEARCH-FINDINGS.md` at the end.

---

## Overnight Execution Design

- **Zero prompts:** `--allowedTools` pre-approves Read, Edit, Write, Glob, Grep
- **Auto-retry:** 1 retry per failed batch (30-second pause before retry)
- **Resilient to failures:** Each batch writes its own file. If batch N fails, batch N+1 still runs.
- **Resumable:** On re-run, script skips batches that already have findings files + completed progress
- **Full logging:** Timestamped log to `06-CLAUDE-LOGS/logs/YYYY-MM-DD-research-orchestrator.log`
- **2-hour timeout per batch:** Prevents infinite hangs

---

## Script Location

```
C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\run_log_research.py
```

---

## Files Created

| File | Purpose |
|------|---------|
| `scripts/run_log_research.py` | Orchestrator script |
| `06-CLAUDE-LOGS/research-batches/FINDINGS-*.md` | Per-batch findings (created at runtime) |
| `06-CLAUDE-LOGS/research-batches/SYNTHESIS.md` | Synthesis (created at runtime) |
| `06-CLAUDE-LOGS/RESEARCH-PROGRESS.md` | Full checkbox tracker (created at runtime) |
| `06-CLAUDE-LOGS/RESEARCH-FINDINGS.md` | Final merged output (created at runtime) |
| `06-CLAUDE-LOGS/logs/YYYY-MM-DD-research-orchestrator.log` | Runtime log |

---

## Estimated Runtime

- **~16 file batches** (sonnet, ~25 files each): ~15-30 min per batch = **4-7.5 hours**
- **1 synthesis batch** (opus): ~20-40 min
- **Total: ~5-8 hours unattended**

---

## Run Command

```bash
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester"
python scripts/run_log_research.py
```

---

## Verification (After Script Completes)

1. `RESEARCH-PROGRESS.md` — all checkboxes marked `[x]`
2. `RESEARCH-FINDINGS.md` — one findings section per file + synthesis at the bottom
3. Synthesis answers all 8 questions from the research prompt
4. Orchestrator log shows all batches completed with exit code 0
5. To retry failures: just run the script again — it skips completed batches
