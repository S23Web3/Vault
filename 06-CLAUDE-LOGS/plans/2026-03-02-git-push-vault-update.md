# Plan: Git Push All New + Updated Files

## Context
Vault has 170 items showing in `git status` (27 modified, ~143 untracked) since the initial commit (`1e1c49b`). User wants everything pushed to `origin` (`git@github.com:S23Web3/Vault.git`) on branch `main`, excluding `.csv` and `.env` files.

## Pre-flight: What .gitignore Already Handles
The existing `.gitignore` already excludes: `*.csv`, `*.env`, `.env`, `*.bak`, `*.parquet`, `*.pyc`, `__pycache__/`, `venv/`, `logs/`, `data/`, `.obsidian/`, `state.json`, `trades.csv`, `Books/`, `*.pkl`, `*.h5`, `*.onnx`, `*.joblib`, `*.tmp`, `*.backup`

## Items Flagged for User Decision

| Item | Count | Concern | Recommendation |
|------|-------|---------|----------------|
| `*.bak.*` files (e.g. `executor.20260226_180119.bak.py`) | 9 | `.gitignore` has `*.bak` but that doesn't match `*.bak.py` or `*.bak.css` | Add `*.bak.*` to `.gitignore` — these are backups, not deliverables |
| `.playwright-mcp/` | 1 dir | Local MCP tool config (console log) | Add to `.gitignore` — machine-specific |
| `.claude/settings.local.json` | 1 file | Local Claude Code permission settings | Add to `.gitignore` — machine-specific |
| `PROJECTS/yt-transcript-analyzer/output/` | 608 files | Generated transcript data (202 .txt, 203 .json, 1 .md, subdirs: chunks, clean, data, findings, raw, reports, summaries) | Add to `.gitignore` — generated output, can be regenerated |

## Execution Steps

### Step 1 — Update `.gitignore` (pending user approval on flagged items)
Add these lines:
```
# Local tool configs
.playwright-mcp/
.claude/settings.local.json

# Backup files with extensions after .bak
*.bak.*

# YT analyzer generated output
PROJECTS/yt-transcript-analyzer/output/
```

### Step 2 — Stage all files
```bash
git add .
```
This will stage ~170 files (after gitignore filtering). The big categories:
- **27 modified files**: CLAUDE.md, bingx-connector core (executor, main, position_monitor, signal_engine, state_manager, risk_gate, config.yaml, plugin), backtester (signals, scripts, docs), yt-analyzer (cleaner, config, fetcher, reporter, requirements.txt), vault meta (INDEX.md, LIVE-SYSTEM-STATUS.md, PRODUCT-BACKLOG.md)
- **~60 session logs**: `06-CLAUDE-LOGS/2026-02-2*.md`
- **~50 plan files**: `06-CLAUDE-LOGS/plans/*.md`
- **~20 bingx-connector new files**: dashboards (v1 through v1-3), ws_listener, screener, scripts, docs, tests
- **~10 backtester new files**: BUILD-VINCE-B1 through B6, docs, scripts, strategies
- **3 yt-analyzer new files**: gui.py, summarizer.py
- **1 vault root**: PROJECT-OVERVIEW.md

### Step 3 — Commit
```bash
git commit -m "Vault update: bingx connector live + dashboards, vince build specs, yt analyzer v2, session logs"
```

### Step 4 — Push
```bash
git push origin main
```

## Permissions Needed
1. **Edit `.gitignore`** — add exclusion lines
2. **`git add .`** — stage all non-ignored files
3. **`git commit`** — create commit
4. **`git push origin main`** — push to remote

## Verification
- `git status` after push shows clean working tree (only ignored files remain)
- `git log -1` shows the new commit
- No `.csv`, `.env`, `.bak.*`, or generated output files in the commit