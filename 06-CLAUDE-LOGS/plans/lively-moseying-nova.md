# Vault to VPS Migration — Step-by-Step Guide

## Why

Bot needs 24/7 uptime. PC can't guarantee that. VPS (Jacky) has 190GB free, 16GB RAM, 4 cores — barely used. ML/data stays on PC (RTX 3060 + 33GB data). Bot runs on VPS.

## Decisions

- One flat repo for entire vault (backtester .git removed)
- No cron — push from PC when work is done, pull on VPS only when deploying
- Private repo: `S23Web3/Vault` (already created)

---

## PART A: Set up git on your PC (run in Git Bash)

### A1. Remove backtester's separate .git

```bash
rm -rf "/c/Users/User/Documents/Obsidian Vault/PROJECTS/four-pillars-backtester/.git"
```

**Check:** `ls "/c/Users/User/Documents/Obsidian Vault/PROJECTS/four-pillars-backtester/.git"` should say "No such file"

### A2. Initialize vault as a git repo

```bash
cd "/c/Users/User/Documents/Obsidian Vault"
git init
```

**Check:** You should see "Initialized empty Git repository"

### A3. Create .gitignore

I will write this file for you (Step 2 of implementation). It excludes:
- 33GB of data directories
- `.env` files (secrets)
- `__pycache__`, `.pyc`
- `Tv.md` (credentials)
- Bot runtime logs
- OS junk, temp files
- Large model binaries (`.pkl`, `.h5`, `.onnx`)

### A4. Stage and commit

```bash
cd "/c/Users/User/Documents/Obsidian Vault"
git add .
git status
```

**Check:** Review the file list. Should be hundreds of `.md` and `.py` files. Should NOT see any `.env`, `.csv`, `.parquet`, or `__pycache__` files. If you see something wrong, tell me and we fix the `.gitignore`.

```bash
git commit -m "Initial vault commit"
```

### A5. Push to GitHub (repo already created)

```bash
git remote add origin git@github.com:S23Web3/Vault.git
git branch -M main
git push -u origin main
```

**Check:** Go to https://github.com/S23Web3/Vault — should now have all your files.

---

## PART B: Set up VPS (run via SSH)

### B1. SSH into Jacky

```bash
ssh root@76.13.20.191
```

### B2. Generate SSH key for GitHub

```bash
ssh-keygen -t ed25519 -C "malik@shortcut23.com"
```

Press Enter for all prompts (default location, no passphrase).

```bash
cat ~/.ssh/id_ed25519.pub
```

**Action:** Copy the output. Go to https://github.com/settings/keys, click "New SSH key", paste it, save.

### B3. Test GitHub connection

```bash
ssh -T git@github.com
```

**Check:** Should say "Hi S23Web3! You've successfully authenticated"

### B4. Clone the vault

```bash
cd /root
git clone git@github.com:S23Web3/Vault.git vault
```

**Check:** `ls /root/vault/PROJECTS/bingx-connector/main.py` should exist.

### B5. Install Python and create venv

```bash
apt update && apt install python3.12 python3.12-venv python3-pip -y
cd /root/vault/PROJECTS/bingx-connector
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Check:** `python --version` shows 3.12.x. `pip list` shows requests, pyyaml, pandas, numpy.

### B6. Create .env file on VPS

```bash
nano /root/vault/PROJECTS/bingx-connector/.env
```

Paste these values (get from your local `.env` at `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\.env`):

```
BINGX_API_KEY=your_key_here
BINGX_SECRET=your_secret_here
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

Save (Ctrl+O, Enter, Ctrl+X). Then lock permissions:

```bash
chmod 600 /root/vault/PROJECTS/bingx-connector/.env
```

### B7. Quick test — does the bot start?

```bash
cd /root/vault/PROJECTS/bingx-connector
source venv/bin/activate
python main.py
```

**Check:** Bot should start, print startup logs, begin warmup. Let it run ~30 seconds to confirm no import errors or crashes. Then Ctrl+C to stop.

### B8. Create systemd service (24/7 auto-restart)

```bash
cat > /etc/systemd/system/bingx-bot.service << 'EOF'
[Unit]
Description=BingX Trading Bot (Four Pillars v3.8.4)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/vault/PROJECTS/bingx-connector
ExecStart=/root/vault/PROJECTS/bingx-connector/venv/bin/python main.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF
```

Then enable and start:

```bash
systemctl daemon-reload
systemctl enable bingx-bot
systemctl start bingx-bot
```

**Check:**

```bash
systemctl status bingx-bot
```

Should show "active (running)". You should also get a Telegram startup alert.

### B9. View live logs

```bash
journalctl -u bingx-bot -f
```

Ctrl+C to stop watching.

---

## PART C: Ongoing workflow

### Push from PC (after a build session)

```bash
cd "/c/Users/User/Documents/Obsidian Vault"
git add .
git commit -m "sync: <what changed>"
git push
```

### Deploy to VPS (only when bot code changed)

```bash
ssh root@76.13.20.191 "cd /root/vault && git pull && systemctl restart bingx-bot"
```

One command. Pull + restart.

### Check bot status anytime

```bash
ssh root@76.13.20.191 "systemctl status bingx-bot"
```

### View recent bot logs

```bash
ssh root@76.13.20.191 "journalctl -u bingx-bot --no-pager -n 50"
```

---

## Architecture

```
PC (Windows)                              VPS (Jacky - Ubuntu 24.04)
- Obsidian Vault (master copy)            - /root/vault (git mirror)
- 33GB data (backtester only)             - BingX bot (systemd, 24/7)
- PostgreSQL (local)                      - n8n + Docker postgres
- Ollama + RTX 3060 (ML)                  - Low latency to BingX (Asia)
- Backtester runs here                    - Telegram alerts
```

## Files to create

1. `C:\Users\User\Documents\Obsidian Vault\scripts\migrate_pc.ps1` — PowerShell script for Part A (run on PC)
2. `C:\Users\User\Documents\Obsidian Vault\scripts\setup_vps.sh` — Bash script for Part B (run on VPS via SSH)
3. `C:\Users\User\Documents\Obsidian Vault\scripts\deploy.ps1` — PowerShell one-liner for Part C (ongoing deploys)
4. `C:\Users\User\Documents\Obsidian Vault\.gitignore` — created by migrate_pc.ps1

All scripts are self-documenting with comments explaining every step. User runs everything manually.
