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

### 2026-03-06 update

- **All 21 file batches COMPLETE overnight.** 353/354 files processed (1 missed in dated-plans-16).
- **RESEARCH-FINDINGS.md** fully merged with all per-batch findings.
- **Synthesis failure:** Batch 22 kept failing with exit code 1. Error: `[synthesis] +38s | Prompt is too long`. Root cause: synthesis prompt told agent to read all 21 individual FINDINGS-*.md files — combined content overflows opus 200K context window.
- **Fix applied (2026-03-06):**
  1. `MAX_TURNS_SYNTHESIS` bumped 100 → 200
  2. `build_synthesis_prompt()` rewritten — reads merged `RESEARCH-FINDINGS.md` (single file, 2000-line chunks) instead of all 21 individual files
- **2026-03-06 re-run:** Script detected dated-plans-16 incomplete (9/10), re-running it before synthesis.

## Run command

```bash
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester"
python scripts/run_log_research.py
```

## Resume after interruption

Script skips batches where FINDINGS-*.md exists AND all files are checked off in RESEARCH-PROGRESS.md. Re-run the same command to resume.

Before re-running from scratch: delete `RESEARCH-PROGRESS.md` and all `research-batches/` files.

---

## Final Run Status — 2026-03-06 18:55:12

**COMPLETE. Zero failures.**

| Metric | Value |
|--------|-------|
| Total batches | 22 (21 file + 1 synthesis) |
| Files processed | 353/354 |
| Skipped (already done) | 19 |
| Re-ran incomplete | 2 (dated-plans-16, auto-plans-18) |
| Failed | 0 |
| Elapsed | 1.2 hours |
| Model | sonnet (batches), opus (synthesis) |

**Outputs:**
- `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\RESEARCH-FINDINGS.md` — full merged output (21 FINDINGS + SYNTHESIS)
- `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\research-batches\SYNTHESIS.md` — standalone synthesis

**Synthesis summary (8 sections):**
1. **Project goal** — Full algo trading system: Four Pillars strategy (Ripster Clouds + AVWAP + Quad Stochastics + BBWP)
2. **Current state** — Backtester v3.8.4 stable, BingX v1.5 live ($110 margin), Vince B2 built/B1 unstarted, BBW layers 1-5 complete, Pine v3.8 stable, PostgreSQL + Ollama + CUDA operational
3. **Primary blocker** — Vince B1 (Phase 0 strategy alignment) — all downstream ML (B3-B10) blocked
4. **Locked decisions** — 16 locked: commission 0.08%, stochastics 9/14/40/60 Raw K, cloud numbering 2-5, 5m > 1m, Vince = Research Engine not classifier, Dash not Streamlit, TTP rules, signal grading A/B/C
5. **Open decisions** — 10 open: Vince B1 feature set, walk-forward windows, coin selection for scale, TTP params, Ollama role, GPU sweep validation, BBW-backtester integration, dynamic position sizing
6. **Confirmed working** — Full backtester pipeline, BingX auth/orders/fills/TTP/BE, BBW layers 1-5, Pine v3.8, all infrastructure
7. **Built but unverified** — v3.9.4 GPU sweep (CUDA parity), multi-coin bot stress test, B2 API (no upstream B1), rebate reconciliation, VPS error recovery
8. **Planned but never executed** — Dynamic position sizing, walk-forward, risk circuit breaker, n8n webhooks, multi-exchange, B3-B10 Vince phases, CI/CD, monitoring, automated backups
