# Plan: Git Push Preparation + Bot Server Readiness

## Context
All work from 2026-03-03 through 2026-03-05 needs to be committed and pushed to the vault repo (GitHub: S23Web3/ni9htw4lker). This includes BingX connector v1.5 patches (timestamp sync fix, TTP engine, config tuning), backtester v391 modules, session logs, build scripts, and documentation updates. The bot will be pulled and run on the VPS tomorrow — VPS is already configured with .env and environment.

## Step 1: Stage all files
- `git add -A` in the vault root
- .gitignore already excludes: `.env`, `data/`, `logs/`, `state.json`, `bot.pid`, `__pycache__/`, `.obsidian/`, ML binaries
- No secrets in any tracked/untracked file (verified: config.yaml has no API keys, bingx_auth.py reads from env vars)

## Step 2: Verify critical bot files are staged
Confirm these are included (essential for bot runtime on VPS):
- `PROJECTS/bingx-connector/main.py` (modified)
- `PROJECTS/bingx-connector/bingx_auth.py` (modified — time_sync import)
- `PROJECTS/bingx-connector/executor.py` (modified)
- `PROJECTS/bingx-connector/position_monitor.py` (modified)
- `PROJECTS/bingx-connector/signal_engine.py` (modified)
- `PROJECTS/bingx-connector/state_manager.py` (modified)
- `PROJECTS/bingx-connector/ws_listener.py` (modified)
- `PROJECTS/bingx-connector/config.yaml` (modified — tuned params)
- `PROJECTS/bingx-connector/time_sync.py` (NEW — critical for 109400 fix)
- `PROJECTS/bingx-connector/main_beta.py` (NEW — beta bot)
- `PROJECTS/bingx-connector/config_beta.yaml` (NEW — beta config)
- `PROJECTS/bingx-connector/bingx-live-dashboard-v1-5.py` (NEW — dashboard)

## Step 3: Commit
Message: `"Vault update: BingX v1.5 (time sync, TTP, config tuning), backtester v391, session logs 2026-03-03 to 2026-03-05"`

## Step 4: Push
- `git push origin main`
- Verify push succeeds

## Step 5: Post-push verification
- `git log --oneline -3` to confirm commit is latest
- `git status` to confirm clean working tree
- Remind user: on VPS, `git pull origin main` then `python main.py`

## Files touched
- **20 modified tracked files** (bot code, config, docs, backtester)
- **70+ new untracked files** (session logs, plans, build scripts, new modules)
- **0 files with secrets** (all verified clean)

## Verification
- After push: `git log --oneline -1` shows new commit
- After push: `git status` shows clean tree
- On VPS: `git pull origin main` + verify `time_sync.py` exists in `PROJECTS/bingx-connector/`
