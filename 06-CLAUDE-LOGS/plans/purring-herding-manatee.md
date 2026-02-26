# Plan: VPS Migration — .gitignore + Deploy Bot

## Context

Bot code is production-ready (67/67 tests, 20.5h stable run, all fixes applied). The 103 trades on 1m lost money as expected (backtester confirms 5m >> 1m for all low-price coins). Config already switched to 5m. User wants to run the bot from VPS (Jacky — 76.13.20.191, Ubuntu 24.04, 190GB free) for 24/7 uptime. The migration guide already exists at `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-02-26-vault-vps-migration.md` — only missing piece is the `.gitignore`.

## What I Build

### 1. Vault-level `.gitignore`

**File**: `C:\Users\User\Documents\Obsidian Vault\.gitignore`

Excludes (~33GB of data + secrets + runtime artifacts):
- `PROJECTS/four-pillars-backtester/data/` (CSV, parquet, cache — bulk of 33GB)
- `trading-tools/data/cache/` (parquet files)
- `Books/` (PDF/EPUB binaries)
- `postgres/` (installer executables)
- `.obsidian/` (Obsidian workspace state, not needed on VPS)
- `Tv.md` (credentials)
- `.env` (all projects)
- `**/__pycache__/`, `*.pyc`, `.pytest_cache/`
- `venv/` (recreated on VPS via requirements.txt)
- `**/logs/` (runtime logs — environment-specific, generated fresh)
- `*.pkl`, `*.h5`, `*.onnx` (ML model binaries)
- `*.parquet`, `*.meta` (data cache files outside data/ dirs)
- `state.json`, `trades.csv` (bot runtime state)
- `.DS_Store`, `Thumbs.db`

Keeps:
- All `.md` files (notes, docs, plans, journals)
- All `.py` files (source code)
- All `.yaml`/`.json` config files
- `requirements.txt` files
- Existing sub-project `.gitignore` files

### 2. Update bingx-connector `.gitignore`

**File**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\.gitignore`

Add `logs/` (currently only has `bot.log`, but bot now writes to `logs/YYYY-MM-DD-bot.log`). Also add `venv/`.

### 3. No code changes needed

Audit script: uses `Path(__file__).resolve()` — cross-platform, works on Linux.
Plugin import: uses `Path(__file__).resolve().parent.parent.parent / "four-pillars-backtester"` — resolves to `/root/vault/PROJECTS/four-pillars-backtester` on VPS. No hardcoded Windows paths.
Bot `main.py`: all paths relative. Logging creates `logs/` dir at startup.

## What the user does after (from the existing migration guide)

1. **Part A** (PC — Git Bash): Remove backtester `.git`, init vault repo, stage + commit, push to `S23Web3/obsidian-vault` (private)
2. **Part B** (VPS — SSH): Clone repo, install Python 3.12 + venv, create `.env`, create systemd service `bingx-bot`, start
3. **Part C** (ongoing): Push from PC after builds, `ssh root@76.13.20.191 "cd /root/vault && git pull && systemctl restart bingx-bot"` to deploy

## Timeline after deploy

- **0-16.7h**: Warmup (201 bars on 5m). No trades.
- **16.7h+**: Signals fire. Trades with real SL/TP exits.
- **After 24h of trading** (~40h total): Run `python scripts/audit_bot.py` on VPS. Should show TP_HIT / SL_HIT instead of EXIT_UNKNOWN.

## Verification

1. After writing `.gitignore`: `git status` should show hundreds of `.md`/`.py` files, zero `.csv`/`.parquet`/`.env` files
2. After VPS clone: `ls /root/vault/PROJECTS/bingx-connector/main.py` exists
3. After bot start: `systemctl status bingx-bot` shows "active (running)" + Telegram startup alert
4. After 24h trading: `python scripts/audit_bot.py` shows real exit reasons (TP_HIT/SL_HIT)
