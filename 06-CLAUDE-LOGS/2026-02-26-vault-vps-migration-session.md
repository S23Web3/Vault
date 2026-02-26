# Vault to VPS Migration — Session Log
**Date:** 2026-02-26
**Topic:** Git repo setup, VPS deployment scripts, daily workflow

---

## What Was Done

### Planning
- Audited VPS specs: 4 cores, 16GB RAM, 190GB free disk, Ubuntu 24.04 (Jacky, 76.13.20.191)
- Assessed vault structure: ~33GB heavy data (parquets, CSVs) stays on PC, ~500MB of source/docs migrates
- Decided: one flat repo (backtester .git removed), manual push-when-ready, no cron
- User created GitHub repo: `S23Web3/Vault` (private)

### Scripts Built
3 scripts written to `C:\Users\User\Documents\Obsidian Vault\scripts\`:

**1. migrate_pc.ps1** (run once on PC, PowerShell)
- Prerequisite check (git, SSH to GitHub)
- Removes backtester/bingx `.git` folders (flat inclusion)
- Creates `.gitignore` (excludes 33GB data, secrets, artifacts)
- Creates `.gitattributes` (LF for .sh/.py/.yaml, CRLF for .ps1)
- Stages, safety-checks for secrets/data leaks, pauses for review, commits, pushes
- Re-run safe: skips commit if already done, goes straight to push

**2. setup_vps.sh** (run once on VPS via SSH)
- CRLF self-fix (if scp'd from Windows)
- SSH key generation + GitHub connection test (smart skip on re-run)
- Clones vault to `/root/vault`
- Installs Python 3.12 + venv + requirements
- Prompts for manual `.env` creation (validates 4 required keys)
- Import test on all bot modules (NOT `import main` which would start the bot)
- Creates systemd service (auto-restart, boot-start, unbuffered logs)
- Starts bot, verifies active status

**3. deploy.ps1** (ongoing use from PC, PowerShell)
- `-Message "text"` — push only (GitHub backup)
- `-Message "text" -Sync` — push + git pull on VPS (no bot restart)
- `-Message "text" -Restart` — push + pull + restart bot (warns about 16.7h warmup cost)
- `-Status` — check bot status
- `-Logs` — view last 50 bot log lines
- `-Rollback` — show VPS commit history, roll back to chosen commit
- Safety check on every push (blocks .env, .csv, .parquet, Tv.md)
- SSH failure recovery guidance (code safe on GitHub, manual fix instructions)
- Git conflict recovery guidance (stash/pull/pop)

### Two Audit Rounds
**Round 1 (code quality):**
- Removed incorrect `gh` prerequisite
- Added prerequisite checks (git, SSH)
- Added pause before commit
- Fixed import test (was importing main.py which starts the bot)
- Showed pip install output (was hidden)
- Added safety check to deploy.ps1
- Added timestamps to all script banners

**Round 2 (lifeline/production):**
- P0: Split deploy into -Sync (files only) vs -Restart (bot restart) to protect 16.7h warmup
- P1: Re-run safety for migrate_pc.ps1 (skip commit if already done)
- P1: Smart skip on setup_vps.sh step 1 (test GitHub first, skip key pause if working)
- P1: Show apt install errors (was hidden)
- P2: SSH failure recovery message with manual fix commands
- P2: Git conflict recovery guidance
- P2: Rollback capability added
- Ubuntu compatibility: .gitattributes for line endings, CRLF self-fix in setup_vps.sh

---

## Files Created
| File | Type |
|------|------|
| `C:\Users\User\Documents\Obsidian Vault\scripts\migrate_pc.ps1` | PowerShell (300 lines) |
| `C:\Users\User\Documents\Obsidian Vault\scripts\setup_vps.sh` | Bash (365 lines) |
| `C:\Users\User\Documents\Obsidian Vault\scripts\deploy.ps1` | PowerShell (138 lines) |
| `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-02-26-vault-vps-migration.md` | Plan doc |

## Files NOT Yet Created (created by scripts at runtime)
| File | Created by |
|------|-----------|
| `C:\Users\User\Documents\Obsidian Vault\.gitignore` | migrate_pc.ps1 |
| `C:\Users\User\Documents\Obsidian Vault\.gitattributes` | migrate_pc.ps1 |
| `/etc/systemd/system/bingx-bot.service` | setup_vps.sh |

---

## Next Steps
1. Run `.\scripts\migrate_pc.ps1` from PowerShell in the vault directory
2. SSH to VPS, upload setup_vps.sh, run it
3. Use `.\scripts\deploy.ps1` for ongoing workflow

## Run Commands
```powershell
# Step 1: Migrate (PC)
cd "C:\Users\User\Documents\Obsidian Vault"
.\scripts\migrate_pc.ps1

# Step 2: Setup VPS
scp "C:\Users\User\Documents\Obsidian Vault\scripts\setup_vps.sh" root@76.13.20.191:/root/
ssh root@76.13.20.191
chmod +x /root/setup_vps.sh
./setup_vps.sh

# Step 3: Ongoing deploys
.\scripts\deploy.ps1 -Message "what changed" -Sync
.\scripts\deploy.ps1 -Message "bot code fix" -Restart
.\scripts\deploy.ps1 -Status
```
