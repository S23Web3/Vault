# Session Log: E: Drive Migration + PC Guardian
Date: 2026-03-14
Topics: File migration, pip export, dead man's switch, BingX bot removal

## What was built

### 1. Migration Script
- `C:\Users\User\Documents\Obsidian Vault\scripts\migrate_to_e_drive.py`
- Copies all files modified since 2026-01-19 to `E:\Obsidian Vault\`
- Mirrors folder structure, preserves timestamps, verifies by file size
- Skips: `.git`, `venv`, `__pycache__`, `node_modules`
- Result: 39,357 files, 56 GB, 0 failures

### 2. Pip Package Exporter
- `C:\Users\User\Documents\Obsidian Vault\scripts\export_pip_packages.py`
- Exports requirements + downloads wheels to `E:\pip-packages\`
- Generates `install_packages.bat` and `install_packages.sh` for offline install on target device
- 64 packages from `.venv312` (including CUDA: nvidia-cuda-nvcc-cu12, nvidia-cuda-runtime-cu12)
- Note: `torch==2.10.0+cu130` failed — not on PyPI, needs manual download from PyTorch index

### 3. Master Script (combines 1+2)
- `C:\Users\User\Documents\Obsidian Vault\scripts\prepare_e_drive.py`
- Runs migration then pip export in sequence
- Skip-existing logic: re-runs only copy new/changed files
- Copies itself to `E:\prepare_e_drive.py`

### 4. Dead Man's Switch
- `C:\Users\User\Documents\Obsidian Vault\scripts\deadman_switch.py`
- Telegram bot: @Bonanza23_BOT (token in script, chat ID: 972431177)
- Email: malik@shortcut23.com (SMTP config in `E:\guardian-config.json`)
- Check interval: 96h default (configurable via /settimer)
- Reply window: 24h default (configurable via /settimer)
- On trigger: deletes `E:\bitlocker-recovery-key.txt`, schedules reboot, C: locked permanently
- Installed as two Windows scheduled tasks: PCGuardian (every 6h) + PCGuardianListener (every 30m)

### 5. Telegram Commands
- `ok` / `alive` / `confirm` / `yes` — auto-resets 96h timer
- `/status` — show current state, timer values, BitLocker key status
- `/reset` — manual timer reset
- `/settimer check <h>` — change check interval (96h standard, 24h/6h/1h for office/travel)
- `/settimer window <h>` — change reply window
- `/lockdown <minutes>` — start manual countdown then lock C:
- `/lockdown cancel` — abort countdown
- `/help` — show all commands

### 6. BingX Bot Startup Removal
- `BingXBot` scheduled task found and removed
- Confirmed absent from: registry Run keys, Startup folder, Task Scheduler

## E: Drive Layout
```
E:\
  Obsidian Vault\          — full mirror of vault (39,357 files, 56 GB)
  pip-packages\            — wheels + install scripts + export script
  migration-log-2026-03-14.txt
  prepare_e_drive.py       — master migration script
  bitlocker-recovery-key.txt  — BitLocker key (guard this)
  deadman-state.json       — guardian timer state
  deadman-offset.json      — Telegram update offset
  deadman-switch.log       — guardian log
  guardian-config.json     — SMTP config (create manually)
```

## Run Commands
```powershell
# Re-run migration (skips existing files)
python "C:\Users\User\Documents\Obsidian Vault\scripts\prepare_e_drive.py"

# Test Telegram
python "C:\Users\User\Documents\Obsidian Vault\scripts\deadman_switch.py" --test

# Test listener interactively
python "C:\Users\User\Documents\Obsidian Vault\scripts\deadman_switch.py" --listen

# Reset alive timer
python "C:\Users\User\Documents\Obsidian Vault\scripts\deadman_switch.py" --reset

# Reinstall tasks after script changes
python "C:\Users\User\Documents\Obsidian Vault\scripts\deadman_switch.py" --install
```

## Outstanding
- `torch==2.10.0+cu130` not downloaded — manually get from download.pytorch.org
- `E:\guardian-config.json` — create manually with Gmail app password to enable email alerts
- BitLocker on C: not yet enabled — run `manage-bde -on C: -RecoveryPassword -SkipHardwareTest` as Admin
