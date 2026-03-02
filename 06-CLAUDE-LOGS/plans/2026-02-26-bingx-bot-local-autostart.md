# Plan: BingX Bot Local Auto-Start with Reboot Persistence

## Context

The VPS (Hostinger, Jakarta) cannot reach BingX's VST (demo) API — `open-api-vst.bingx.com` resolves to Indonesian IPs that block datacenter connections. The live API (`open-api.bingx.com`) works fine on VPS via CloudFront CDN. Since the user wants to run demo mode first (47 coins, 5m chart, "let it burn VST"), the bot must run locally on the Windows PC.

The bot needs to survive power cuts (auto-start on reboot) and auto-restart on crashes. The bot code itself already has full signal + error logging — no code changes needed to main.py or any bot modules.

## What Already Works (No Changes Needed)

- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main.py` — full bot with dual-thread architecture
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\config.yaml` — 47 coins, 5m timeframe, demo_mode: true
- Signal logging: every signal detected, blocked, executed logged at INFO level
- Error logging: plugin errors, execution failures logged at ERROR level
- Dual output: file (`logs/YYYY-MM-DD-bot.log`) + console, timestamped UTC+4

## Deliverables

### 1. Wrapper script: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\run_bot.ps1`

PowerShell wrapper that:
- Activates the venv (if exists) or uses system Python
- Runs `main.py`
- On crash: logs the crash, waits 30 seconds, restarts
- Infinite restart loop until manually stopped
- Logs wrapper-level events (start, crash, restart) to `logs/YYYY-MM-DD-wrapper.log`

```powershell
# Pseudo-structure:
while ($true) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Output "$timestamp [WRAPPER] Starting bot..."

    # Run main.py, capture exit code
    python main.py
    $exitCode = $LASTEXITCODE

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Output "$timestamp [WRAPPER] Bot exited with code $exitCode. Restarting in 30s..."
    Start-Sleep -Seconds 30
}
```

### 2. Task Scheduler XML: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\bingx-bot-task.xml`

Windows Task Scheduler task that:
- **Trigger**: At system startup (survives reboots/power cuts)
- **Action**: Run `run_bot.ps1` (which handles crash recovery)
- **Settings**: Run whether user is logged on or not, run with highest privileges
- **No stop on idle**: keeps running even if PC is idle

### 3. Install/uninstall helper: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\install_autostart.ps1`

One-shot script the user runs to register the Task Scheduler task. Also includes an uninstall command.

```powershell
# Install:
schtasks /create /tn "BingXBot" /xml "bingx-bot-task.xml" /f

# Uninstall:
# schtasks /delete /tn "BingXBot" /f
```

## Files to Create

| File | Purpose |
|------|---------|
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\run_bot.ps1` | Wrapper: crash recovery + restart loop |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\bingx-bot-task.xml` | Task Scheduler definition |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\install_autostart.ps1` | Register/unregister the scheduled task |

## Files NOT Modified

- `main.py` — no changes
- `config.yaml` — no changes (already 47 coins, 5m, demo_mode: true)
- `signal_engine.py` — already logs all signals at INFO
- All other bot modules — untouched

## Verification

1. User runs `install_autostart.ps1` from admin PowerShell
2. User opens Task Scheduler GUI and confirms "BingXBot" task exists
3. User runs `run_bot.ps1` manually first to verify it starts the bot
4. User reboots PC and checks:
   - Bot auto-started (check `logs/YYYY-MM-DD-bot.log` for startup entry)
   - Wrapper running (check `logs/YYYY-MM-DD-wrapper.log`)
5. To test crash recovery: kill `python.exe` from Task Manager, confirm wrapper restarts it within 30s
6. Monitor signals in logs: `Get-Content -Wait "logs\*-bot.log"` (tail -f equivalent)

## Commands for User

```powershell
# Install auto-start (run once, as admin):
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\install_autostart.ps1"

# Manual start (for testing):
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\run_bot.ps1"

# Check logs:
Get-Content -Wait "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\logs\*-bot.log"

# Stop:
# Kill from Task Manager or: schtasks /end /tn "BingXBot"

# Uninstall auto-start:
schtasks /delete /tn "BingXBot" /f
```
