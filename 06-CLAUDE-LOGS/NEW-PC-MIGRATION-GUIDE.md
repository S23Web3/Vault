# New PC Migration Guide
Generated: 2026-03-14
Purpose: Complete instructions to set up a new PC as main machine with all systems running.

---

## What you are migrating
- Obsidian Vault (all projects, scripts, logs) — from E: drive
- Python environment (.venv312, 64 packages including CUDA)
- Git repo (four-pillars-backtester, connected to GitHub)
- Dead man's switch (PCGuardian Telegram bot)
- E: drive auto-sync watcher
- Daily 9pm milestone push
- BingX / WEEX connector bots
- Ollama (local LLM)
- PostgreSQL 16 (vince database)

---

## Step 1 — Windows auto-login (do this first)

Removes the password prompt on startup so the PC boots straight to desktop.

```powershell
# Run as Administrator
# Replace YOUR_PASSWORD with your Windows login password
$username = $env:USERNAME
$password = "YOUR_PASSWORD"
$registryPath = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"
Set-ItemProperty $registryPath "AutoAdminLogon" -Value "1"
Set-ItemProperty $registryPath "DefaultUsername" -Value $username
Set-ItemProperty $registryPath "DefaultPassword" -Value $password
Set-ItemProperty $registryPath "DefaultDomainName" -Value $env:COMPUTERNAME
```

Or via GUI:
1. Win+R → `netplwiz`
2. Uncheck "Users must enter a username and password"
3. Enter your password when prompted
4. Reboot — boots straight to desktop

---

## Step 2 — Install prerequisites

### Python 3.12
- Download from python.org — get 3.12.x (same as .venv312)
- During install: check "Add Python to PATH"
- Verify: `python --version` → should say 3.12.x

### Git
- Download from git-scm.com
- Default options are fine
- Set identity:
```powershell
git config --global user.name "S23Web3"
git config --global user.email "malik@shortcut23.com"
```

### GitHub SSH key (so git push works without password)
```powershell
ssh-keygen -t ed25519 -C "malik@shortcut23.com"
# Press Enter for all prompts (default location, no passphrase)
cat C:\Users\User\.ssh\id_ed25519.pub
# Copy the output, go to github.com/settings/keys, add new SSH key, paste it
```

### NVIDIA CUDA drivers
- Download from nvidia.com — match your GPU model
- Required for PyTorch GPU inference

### Ollama
- Download from ollama.com
- After install: `ollama pull qwen3:8b`

### PostgreSQL 16
- Download from postgresql.org
- Install on port 5433, user=postgres, password=admin
- After install, restore schema:
```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -p 5433 -f "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\postgres\schema.sql"
```

---

## Step 3 — Copy vault from E: drive

Plug in the E: drive (enter BitLocker password when prompted).

```powershell
# Copy entire vault to same path as old PC
xcopy "E:\Obsidian Vault" "C:\Users\User\Documents\Obsidian Vault" /E /H /I /Y
```

Or use the migration script already on E::
```powershell
# This copies E: → C: (reverse of normal direction)
# Manually copy or use File Explorer: E:\Obsidian Vault → C:\Users\User\Documents\
```

---

## Step 4 — Restore Python environment

```powershell
# Navigate to backtester project
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester"

# Create new venv
python -m venv .venv312

# Activate it
.venv312\Scripts\activate

# Install all packages from E: drive (offline, no internet needed)
pip install --no-index --find-links "E:\pip-packages\packages-four-pillars-backtester" -r "E:\pip-packages\requirements-four-pillars-backtester.txt"

# Verify
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```

Note: `torch==2.10.0+cu130` may need manual download from:
`https://download.pytorch.org/whl/cu130`

---

## Step 5 — Clone / link git repo

```powershell
# If vault was copied in Step 3, just re-link the remote:
cd "C:\Users\User\Documents\Obsidian Vault"
git remote set-url origin git@github.com:S23Web3/ni9htw4lker.git

# Verify
git remote -v
git status
```

---

## Step 6 — Install scheduled tasks

Run each install command as Administrator:

```powershell
# Dead man's switch (PCGuardian + PCGuardianListener)
python "C:\Users\User\Documents\Obsidian Vault\scripts\deadman_switch.py" --install

# Daily 9pm milestone push (MilestonePush)
python "C:\Users\User\Documents\Obsidian Vault\scripts\milestone_push.py" --install

# E: drive USB watcher (EDriveWatcher)
python "C:\Users\User\Documents\Obsidian Vault\scripts\e_drive_watcher.py" --install
```

Verify all tasks registered:
```powershell
Get-ScheduledTask | Where-Object {$_.TaskPath -notlike "\Microsoft\*"} | Select-Object TaskName, State
```

Expected: PCGuardian, PCGuardianListener, MilestonePush, EDriveWatcher all showing Ready.

---

## Step 7 — Install WMI module (needed for E: watcher)

```powershell
pip install wmi pywin32
```

---

## Step 8 — Configure dead man's switch

The Telegram bot token and chat ID are already in the script — no changes needed.

Create the email config file manually:
```
E:\guardian-config.json
```
```json
{
  "smtp_host": "smtp.gmail.com",
  "smtp_port": 587,
  "smtp_user": "malik@shortcut23.com",
  "smtp_pass": "YOUR_GMAIL_APP_PASSWORD"
}
```

Test it:
```powershell
python "C:\Users\User\Documents\Obsidian Vault\scripts\deadman_switch.py" --test
```

Reset the timer so it starts fresh:
```powershell
python "C:\Users\User\Documents\Obsidian Vault\scripts\deadman_switch.py" --reset
```

---

## Step 9 — Enable BitLocker on C: (new PC)

```powershell
# Run as Administrator
manage-bde -on C: -RecoveryPassword -SkipHardwareTest
manage-bde -protectors -get C:
# Copy the recovery key shown → save to E:\bitlocker-recovery-key.txt
```

Enable E: auto-unlock on this PC:
```powershell
manage-bde -autounlock -enable E:
```

---

## Step 10 — Verify everything works

```powershell
# 1. Test Telegram guardian
python "C:\Users\User\Documents\Obsidian Vault\scripts\deadman_switch.py" --test

# 2. Test dry-run milestone push
python "C:\Users\User\Documents\Obsidian Vault\scripts\milestone_push.py" --dry-run

# 3. Test E: watcher (plug in drive, watch log)
Get-Content "C:\Users\User\Documents\Obsidian Vault\logs\e-drive-watcher.log" -Wait

# 4. Test git push
cd "C:\Users\User\Documents\Obsidian Vault"
git push origin main

# 5. Verify scheduled tasks running
Get-ScheduledTask | Where-Object {$_.TaskPath -notlike "\Microsoft\*"} | Select-Object TaskName, State
```

---

## Checklist

- [ ] Windows auto-login configured
- [ ] Python 3.12 installed + on PATH
- [ ] Git installed + identity set
- [ ] GitHub SSH key added
- [ ] NVIDIA CUDA drivers installed
- [ ] Ollama installed + qwen3:8b pulled
- [ ] PostgreSQL 16 on port 5433
- [ ] Vault copied from E: to C:
- [ ] .venv312 created + packages installed
- [ ] Git remote linked to GitHub
- [ ] PCGuardian task installed
- [ ] PCGuardianListener task installed
- [ ] MilestonePush task installed
- [ ] EDriveWatcher task installed
- [ ] E:\guardian-config.json created
- [ ] Dead man's switch tested (Telegram message received)
- [ ] BitLocker on C: enabled + key saved to E:
- [ ] E: auto-unlock enabled
- [ ] Milestone push dry-run passed
- [ ] Git push working

---

## Files on E: drive (source of truth)

| File | Purpose |
|------|---------|
| `E:\Obsidian Vault\` | Full vault backup |
| `E:\pip-packages\` | All Python wheels for offline install |
| `E:\prepare_e_drive.py` | Master migration script |
| `E:\deadman_switch.py` | Guardian script (latest) |
| `E:\milestone_push.py` | Daily push script |
| `E:\bitlocker-recovery-key.txt` | C: BitLocker key |
| `E:\deadman-state.json` | Guardian timer state |
| `E:\guardian-config.json` | Email SMTP config (create manually) |
| `E:\session-log-2026-03-14-migration-guardian.md` | This session log |
