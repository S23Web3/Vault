# Plan: Claude Desktop Daily Brief — Twice-Daily Sync

**Date:** 2026-03-14

## Context

Claude Desktop has no visibility into what happened in recent Claude Code sessions. The session logs in `06-CLAUDE-LOGS/` and `PROJECT-STATUS.md` are the source of truth, but Claude Desktop only sees them if they're explicitly loaded. Goal: auto-generate a `CLAUDE-DESKTOP-BRIEF.md` file twice daily (08:00 + 20:00) that Claude Desktop can read at session start to get fully up to date — no manual steps required.

---

## What the brief includes

1. **Recent session logs** — last 7 days of summaries pulled from `INDEX.md` (the table rows, verbatim)
2. **PROJECT-STATUS.md snapshot** — "What is done and working" table + "One-line summary" footer
3. **Open decisions** — the open decisions list from PROJECT-STATUS.md
4. **PRODUCT-BACKLOG.md P0 items** — top priority tasks and their current status

---

## Implementation

### New file: `scripts/build_daily_brief.py`

Single script. No external dependencies beyond stdlib. Pattern mirrors `milestone_push.py` (logging, argparse, install/uninstall).

**Logic:**
1. Parse `06-CLAUDE-LOGS/INDEX.md` — extract all table rows from the last 7 days (look for `### YYYY-MM-DD` headers, collect rows until next header or EOF)
2. Read `06-CLAUDE-LOGS/PROJECT-STATUS.md` — extract two sections: "What is done and working" table, "One-line summary" line
3. Read `PRODUCT-BACKLOG.md` — extract P0 section (lines between `## P0` and next `## P` heading)
4. Read `PROJECT-STATUS.md` — extract "Open decisions" section
5. Write assembled content to `06-CLAUDE-LOGS/CLAUDE-DESKTOP-BRIEF.md` (overwrite each run)
6. Log run result to `logs/YYYY-MM-DD-brief.log`

**Args:**
- `--dry-run` — print output to stdout, don't write file
- `--install` — register Windows scheduled task (same pattern as milestone_push.py)
- `--uninstall` — remove task

**Scheduled task:** `ClaudeDesktopBrief`
- Trigger 1: daily 08:00
- Trigger 2: daily 20:00
- Command: `python "C:\Users\User\Documents\Obsidian Vault\scripts\build_daily_brief.py"`

### Output file: `06-CLAUDE-LOGS/CLAUDE-DESKTOP-BRIEF.md`

```
# Claude Desktop Brief
*Generated: YYYY-MM-DD HH:MM*

## One-line project summary
<from PROJECT-STATUS.md footer>

## Recent sessions (last 7 days)
<INDEX.md table rows for last 7 days, newest first>

## What is working
<"What is done and working" table from PROJECT-STATUS.md>

## P0 Backlog
<P0 section from PRODUCT-BACKLOG.md>

## Open decisions
<Open decisions list from PROJECT-STATUS.md>
```

### MEMORY.md addition

Add one line to the STARTUP section in MEMORY.md:
> 5. Read `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\CLAUDE-DESKTOP-BRIEF.md` for the latest session summary (auto-updated twice daily at 08:00 and 20:00).

---

## Critical files

| File | Action |
|------|--------|
| `C:\Users\User\Documents\Obsidian Vault\scripts\build_daily_brief.py` | CREATE (new script) |
| `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\CLAUDE-DESKTOP-BRIEF.md` | GENERATED OUTPUT (overwritten each run) |
| `C:\Users\User\.claude\projects\c--Users-User-Documents-Obsidian-Vault\memory\MEMORY.md` | EDIT — append startup step 5 |

**Source files read (no changes):**
- `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\INDEX.md`
- `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\PROJECT-STATUS.md`
- `C:\Users\User\Documents\Obsidian Vault\PRODUCT-BACKLOG.md`

---

## Reused patterns

- Scheduled task XML install/uninstall — copied from `scripts/milestone_push.py:181-242`
- Dual-handler logging setup — copied from `scripts/milestone_push.py:41-59`
- `SKIP_DIRS` / path pattern — same vault root constants

---

## Verification

1. Run `python scripts/build_daily_brief.py --dry-run` — confirm output printed to stdout with correct sections
2. Run without `--dry-run` — confirm `06-CLAUDE-LOGS/CLAUDE-DESKTOP-BRIEF.md` created
3. `py_compile` must pass before delivery
4. Run `python scripts/build_daily_brief.py --install` — confirm task `ClaudeDesktopBrief` appears in Task Scheduler with two daily triggers
5. Open `CLAUDE-DESKTOP-BRIEF.md` in Obsidian — confirm it renders cleanly and all 4 sections are present