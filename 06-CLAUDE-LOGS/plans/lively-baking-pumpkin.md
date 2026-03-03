# Plan: Git Cleanup — .gitignore + Backlog Commit

**Date:** 2026-03-03
**Context:** VSCode warning "too many active changes" due to untracked files, particularly `.venv312/` (thousands of files), 37 `.bak*` backup files, and runtime artifacts. Goal: fix .gitignore rules, stage and commit the legitimate backlog, and leave the repo clean.

---

## Scope

1. Update `.gitignore` — add missing patterns for venv variants, bot runtime files, and bak files
2. Keep `.bak*` files on disk but exclude from git
3. Stage + commit all legitimate untracked/modified files as a single backlog commit
4. Plans directory (`06-CLAUDE-LOGS/plans/`) — TRACK in git (commit it)

---

## Step 1 — Update root `.gitignore`

**File:** `C:\Users\User\Documents\Obsidian Vault\.gitignore`

Add the following patterns (append to existing file, do NOT overwrite):

```
# Virtual environments — all common naming variants
.venv/
.venv312/
.venv*/
venv*/
env/
.env/

# BingX connector runtime state
PROJECTS/bingx-connector/bot.pid
PROJECTS/bingx-connector/bot-status.json

# Build backup files (timestamped safety copies, all projects)
*.bak.*
*.bak.py
*.bak.css
*.bak.js
```

Note: The root `.gitignore` already has `**/venv/` but NOT `.venv312/` — the leading dot makes it a different pattern.

---

## Step 2 — Commit the backlog

After `.gitignore` is updated, stage and commit everything that remains untracked or modified. The commit should include:

- All `06-CLAUDE-LOGS/` files (session logs, INDEX.md, plans/)
- All `PROJECTS/bingx-connector/` source files (dashboards, scripts, ttp_engine, tests, docs)
- All `PROJECTS/four-pillars-backtester/` new files (engine, signals, scripts, docs, vince/)
- Modified files: `PRODUCT-BACKLOG.md`, dashboard/connector source files

**Excluded by .gitignore (will NOT be staged):**
- `PROJECTS/four-pillars-backtester/.venv312/`
- `PROJECTS/bingx-connector/bot.pid`
- `PROJECTS/bingx-connector/bot-status.json`
- All 37 `.bak*` files

**Commit message:**
```
Backlog commit: bingx-connector v1.4, backtester engine updates, session logs 2026-02-28 to 2026-03-03

- BingX connector: dashboard v1.3/v1.4, TTP engine, position monitor, signal engine
- Four Pillars backtester: CUDA sweep engine, JIT backtest, strategy analysis reports
- Session logs: 10+ build sessions indexed in 06-CLAUDE-LOGS/
- Product backlog updated
```

---

## Critical files being modified

| File | Change |
|------|--------|
| `C:\Users\User\Documents\Obsidian Vault\.gitignore` | Append 8 new lines |

---

## Execution order

1. Edit root `.gitignore` — append new patterns
2. Run `git status` to confirm `.venv312/` and `.bak*` files are now ignored
3. Run `git add` for all remaining untracked/modified files (excluding ignored)
4. Run `git commit` with the backlog message
5. Run `git status` to confirm clean working tree

---

## Verification

- `git status` after `.gitignore` edit should show `.venv312/` gone from untracked list
- `git status` after commit should show `nothing to commit, working tree clean` (or only `.bak*` files which are intentionally untracked)
- VSCode Git panel should no longer show the "too many active changes" warning
