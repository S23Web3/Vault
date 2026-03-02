# Plan: BingX Bot Local Auto-Start + Telegram Formatting

## Context

VPS (Hostinger Jakarta) cannot reach BingX VST API (`open-api-vst.bingx.com` — Indonesian IPs block datacenter connections). Live API works fine. User wants demo mode first (47 coins, 5m, "let it burn VST"), so the bot runs locally on Windows PC.

Two deliverables:

1. Auto-start on reboot with crash recovery (Windows Task Scheduler)
2. Better Telegram message formatting (currently ugly single-line dumps)

## Build Script

**One script does everything:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_autostart_and_tg.py`

The script:

1. Backs up 3 existing files (timestamped `.bak` copies)
2. Creates 3 new files (wrapper, XML, installer)
3. Modifies 3 existing files (TG formatting)
4. py_compile validates every .py file touched
5. Reports pass/fail summary

### What it creates

| New File | Purpose |
| --- | --- |
| `scripts\run_bot.ps1` | PowerShell wrapper: crash recovery loop, wrapper log |
| `scripts\bingx-bot-task.xml` | Task Scheduler definition: start on boot |
| `scripts\install_autostart.ps1` | One-shot: register/verify/unregister task |

### What it modifies (with backups)

| File | Changes |
| --- | --- |
| `executor.py` | 3 notifier.send calls: ENTRY, ORDER FAILED, ORDER ID UNKNOWN |
| `position_monitor.py` | 4 notifier.send calls: EXIT, DAILY SUMMARY, HARD STOP, WARNING |
| `main.py` | 3 notifier.send calls: STARTUP, SHUTTING DOWN, STOPPED |

### Exact replacements (old -> new)

**executor.py line 177** — ORDER FAILED:
```
OLD: self.notifier.send("ORDER FAILED: " + side + " " + symbol)
NEW: self.notifier.send("<b>ORDER FAILED</b>\n" + side + " " + symbol)
```

**executor.py lines 187-189** — ORDER ID UNKNOWN:
```
OLD: self.notifier.send(
                "ORDER ID UNKNOWN: " + side + " " + symbol
                + " — position NOT tracked")
NEW: self.notifier.send(
                "<b>ORDER ID UNKNOWN</b>\n" + side + " " + symbol
                + "\nPosition NOT tracked")
```

**executor.py lines 206-213** — ENTRY:
```
OLD: entry_msg = ("ENTRY: " + side + " " + symbol
                     + " qty=" + str(round(quantity, 6))
                     + " price=" + str(round(mark_price, 6))
                     + " SL=" + str(round(signal.sl_price, 6))
                     + " grade=" + signal.grade)
        if signal.tp_price is not None:
            entry_msg += " TP=" + str(round(signal.tp_price, 6))

NEW: entry_msg = ("<b>ENTRY</b>  " + side + " " + symbol
                     + "\nGrade: " + signal.grade
                     + "\nQty: " + str(round(quantity, 6))
                     + "  Price: " + str(round(mark_price, 6))
                     + "\nSL: " + str(round(signal.sl_price, 6)))
        if signal.tp_price is not None:
            entry_msg += "  TP: " + str(round(signal.tp_price, 6))
```

**position_monitor.py lines 275-277** — HARD STOP:
```
OLD: self.notifier.send(
                "HARD STOP: daily loss limit ($"
                + str(round(abs(current["daily_pnl"]), 2)) + ")")
NEW: self.notifier.send(
                "<b>HARD STOP</b>\nDaily loss limit: $"
                + str(round(abs(current["daily_pnl"]), 2)))
```

**position_monitor.py lines 278-283** — EXIT:
```
OLD: msg = ("EXIT: " + key
               + " reason=" + exit_reason
               + " pnl=" + str(round(pnl_net, 2))
               + " daily=" + str(round(
                   current.get("daily_pnl", 0), 2)))
NEW: msg = ("<b>EXIT</b>  " + key
               + "\nReason: " + exit_reason
               + "\nPnL: $" + str(round(pnl_net, 2))
               + "\nDaily: $" + str(round(
                   current.get("daily_pnl", 0), 2)))
```

**position_monitor.py lines 298-302** — DAILY SUMMARY:
```
OLD: summary = ("DAILY SUMMARY: pnl="
                       + str(round(daily_pnl, 2))
                       + " trades=" + str(daily_trades)
                       + " open=" + str(open_count))
NEW: summary = ("<b>DAILY SUMMARY</b>"
                       + "\nPnL: $" + str(round(daily_pnl, 2))
                       + "\nTrades: " + str(daily_trades)
                       + "\nOpen: " + str(open_count))
```

**position_monitor.py lines 322-328** — WARNING:
```
OLD: self.notifier.send(
                "WARNING: daily loss at "
                + str(round(pct_of_limit, 1))
                + "% of limit ($"
                + str(round(abs(daily_pnl), 2))
                + " / $" + str(round(self.daily_loss_limit, 2))
                + ")")
NEW: self.notifier.send(
                "<b>WARNING</b>\nDaily loss at "
                + str(round(pct_of_limit, 1))
                + "% of limit\n$"
                + str(round(abs(daily_pnl), 2))
                + " / $" + str(round(self.daily_loss_limit, 2)))
```

**main.py lines 218-222** — STARTUP:
```
OLD: start_msg = ("Bot started: "
                 + str(len(symbols)) + " coins, "
                 + str(open_count) + " open, "
                 + ("DEMO" if demo_mode else "LIVE"))
NEW: start_msg = ("<b>BOT STARTED</b>"
                 + "\nCoins: " + str(len(symbols))
                 + "\nOpen: " + str(open_count)
                 + "\nMode: " + ("DEMO" if demo_mode else "LIVE"))
```

**main.py line 250** — SHUTTING DOWN:
```
OLD: notifier.send("Bot shutting down — waiting for in-flight ops...")
NEW: notifier.send("<b>BOT STOPPING</b>\nWaiting for in-flight ops...")
```

**main.py line 256** — STOPPED:
```
OLD: notifier.send("Bot stopped")
NEW: notifier.send("<b>BOT STOPPED</b>")
```

### run_bot.ps1 content

```powershell
# run_bot.ps1 — BingX bot wrapper with crash recovery
# Restarts the bot on crash. Logs wrapper events to logs\YYYY-MM-DD-wrapper.log.
# Kill this process or Ctrl+C to stop permanently.

$botDir = "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector"
$logDir = Join-Path $botDir "logs"
$mainPy = Join-Path $botDir "main.py"

if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }

function Write-WrapperLog($msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logFile = Join-Path $logDir ((Get-Date -Format "yyyy-MM-dd") + "-wrapper.log")
    $line = "$ts [WRAPPER] $msg"
    Write-Host $line
    Add-Content -Path $logFile -Value $line
}

Set-Location $botDir

# Use venv python if it exists, otherwise system python
$venvPython = Join-Path $botDir "venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    $python = $venvPython
    Write-WrapperLog "Using venv python: $venvPython"
} else {
    $python = "python"
    Write-WrapperLog "Using system python"
}

$restartCount = 0
while ($true) {
    $restartCount++
    Write-WrapperLog "Starting bot (attempt $restartCount)..."

    & $python $mainPy
    $exitCode = $LASTEXITCODE

    Write-WrapperLog "Bot exited with code $exitCode"

    if ($exitCode -eq 0) {
        Write-WrapperLog "Clean exit (code 0). Not restarting."
        break
    }

    Write-WrapperLog "Crash detected. Restarting in 30 seconds..."
    Start-Sleep -Seconds 30
}

Write-WrapperLog "Wrapper exiting."
```

Note: clean exit (code 0) = intentional stop (Ctrl+C / SIGTERM) = don't restart. Non-zero = crash = restart after 30s.

### bingx-bot-task.xml content

Standard Task Scheduler XML:
- Trigger: AtStartup (delay 60s for network to come up)
- Action: powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File "...\run_bot.ps1"
- Settings: run whether logged on or not, don't stop on idle, no execution time limit

### install_autostart.ps1 content

```powershell
# install_autostart.ps1 — Register BingXBot as a scheduled task
# Run as admin: powershell -ExecutionPolicy Bypass -File install_autostart.ps1
# To uninstall: schtasks /delete /tn "BingXBot" /f

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$xmlPath = Join-Path $scriptDir "bingx-bot-task.xml"

# Check admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: Run this script as Administrator."
    exit 1
}

# Check XML exists
if (-not (Test-Path $xmlPath)) {
    Write-Host "ERROR: $xmlPath not found."
    exit 1
}

# Register task
schtasks /create /tn "BingXBot" /xml $xmlPath /f
if ($LASTEXITCODE -eq 0) {
    Write-Host "SUCCESS: BingXBot task registered."
    Write-Host "  It will auto-start on reboot."
    Write-Host "  To start now: schtasks /run /tn BingXBot"
    Write-Host "  To remove:    schtasks /delete /tn BingXBot /f"
} else {
    Write-Host "FAILED: Could not register task."
}
```

## Verification (user runs)

```powershell
# 1. Run build script:
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_autostart_and_tg.py"

# 2. Test bot manually (Ctrl+C to stop):
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\run_bot.ps1"

# 3. Verify TG messages look right (check Telegram after a signal fires or on startup)

# 4. Install auto-start (as admin):
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\install_autostart.ps1"

# 5. Verify in Task Scheduler GUI: "BingXBot" task exists

# 6. Reboot and confirm bot auto-started:
Get-Content -Wait "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\logs\*-bot.log"

# 7. Test crash recovery: kill python.exe, check wrapper restarts in 30s

# Uninstall if needed:
schtasks /delete /tn "BingXBot" /f
```
