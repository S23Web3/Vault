"""
Build script: BingX bot auto-start + Telegram formatting.
Creates 3 new files, modifies 3 existing files (with backups), validates all.
Run: python scripts/build_autostart_and_tg.py
"""

import os
import sys
import shutil
import py_compile
from pathlib import Path
from datetime import datetime

BOT_DIR = Path(r"C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector")
SCRIPTS_DIR = BOT_DIR / "scripts"
ERRORS = []
CREATED = []
MODIFIED = []
BACKED_UP = []


def log(msg):
    """Print timestamped build message."""
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " " + msg)


def backup_file(filepath):
    """Create timestamped backup before modifying."""
    if filepath.exists():
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = filepath.parent / (filepath.stem + "." + ts + ".bak" + filepath.suffix)
        shutil.copy2(filepath, backup)
        BACKED_UP.append(str(backup))
        log("  Backed up: " + str(backup.name))
        return True
    ERRORS.append("BACKUP FAIL: " + str(filepath) + " does not exist")
    return False


def replace_in_file(filepath, old, new):
    """Replace exact string in file. Returns True if replacement was made."""
    content = filepath.read_text(encoding="utf-8")
    if old not in content:
        ERRORS.append("NOT FOUND in " + filepath.name + ": " + repr(old[:80]))
        return False
    count = content.count(old)
    if count > 1:
        ERRORS.append("AMBIGUOUS in " + filepath.name + ": found " + str(count) + " times: " + repr(old[:80]))
        return False
    content = content.replace(old, new, 1)
    filepath.write_text(content, encoding="utf-8")
    return True


def validate_py(filepath):
    """Run py_compile check on a Python file."""
    try:
        py_compile.compile(str(filepath), doraise=True)
        log("  py_compile PASS: " + filepath.name)
        return True
    except py_compile.PyCompileError as e:
        ERRORS.append("py_compile FAIL: " + filepath.name + " -- " + str(e))
        log("  py_compile FAIL: " + filepath.name)
        return False


def write_new_file(filepath, content, description):
    """Write a new file, checking it doesn't already exist."""
    if filepath.exists():
        ERRORS.append("ALREADY EXISTS: " + str(filepath) + " -- not overwriting")
        return False
    filepath.write_text(content, encoding="utf-8")
    CREATED.append(str(filepath))
    log("  Created: " + str(filepath.name) + " (" + description + ")")
    return True


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run the full build."""
    log("=" * 60)
    log("BUILD: BingX Bot Auto-Start + Telegram Formatting")
    log("=" * 60)

    # ------------------------------------------------------------------
    # STEP 1: Create new files
    # ------------------------------------------------------------------
    log("")
    log("[STEP 1/4] Creating new files...")

    # --- run_bot.ps1 ---
    run_bot_ps1 = SCRIPTS_DIR / "run_bot.ps1"
    write_new_file(run_bot_ps1, RUN_BOT_PS1_CONTENT, "PowerShell wrapper")

    # --- bingx-bot-task.xml ---
    task_xml = SCRIPTS_DIR / "bingx-bot-task.xml"
    write_new_file(task_xml, TASK_XML_CONTENT, "Task Scheduler XML")

    # --- install_autostart.ps1 ---
    install_ps1 = SCRIPTS_DIR / "install_autostart.ps1"
    write_new_file(install_ps1, INSTALL_PS1_CONTENT, "Task installer")

    # ------------------------------------------------------------------
    # STEP 2: Backup existing files
    # ------------------------------------------------------------------
    log("")
    log("[STEP 2/4] Backing up existing files...")

    executor_py = BOT_DIR / "executor.py"
    monitor_py = BOT_DIR / "position_monitor.py"
    main_py = BOT_DIR / "main.py"

    backup_file(executor_py)
    backup_file(monitor_py)
    backup_file(main_py)

    # ------------------------------------------------------------------
    # STEP 3: Apply Telegram formatting changes
    # ------------------------------------------------------------------
    log("")
    log("[STEP 3/4] Applying Telegram formatting...")

    # --- executor.py: ORDER FAILED (line 177) ---
    ok = replace_in_file(
        executor_py,
        'self.notifier.send("ORDER FAILED: " + side + " " + symbol)',
        'self.notifier.send("<b>ORDER FAILED</b>\\n" + side + " " + symbol)',
    )
    if ok:
        log("  executor.py: ORDER FAILED -- done")

    # --- executor.py: ORDER ID UNKNOWN (lines 187-189) ---
    ok = replace_in_file(
        executor_py,
        'self.notifier.send(\n'
        '                "ORDER ID UNKNOWN: " + side + " " + symbol\n'
        '                + " \u2014 position NOT tracked")',
        'self.notifier.send(\n'
        '                "<b>ORDER ID UNKNOWN</b>\\n" + side + " " + symbol\n'
        '                + "\\nPosition NOT tracked")',
    )
    if ok:
        log("  executor.py: ORDER ID UNKNOWN -- done")

    # --- executor.py: ENTRY (lines 206-212) ---
    ok = replace_in_file(
        executor_py,
        'entry_msg = ("ENTRY: " + side + " " + symbol\n'
        '                     + " qty=" + str(round(quantity, 6))\n'
        '                     + " price=" + str(round(mark_price, 6))\n'
        '                     + " SL=" + str(round(signal.sl_price, 6))\n'
        '                     + " grade=" + signal.grade)\n'
        '        if signal.tp_price is not None:\n'
        '            entry_msg += " TP=" + str(round(signal.tp_price, 6))',
        'entry_msg = ("<b>ENTRY</b>  " + side + " " + symbol\n'
        '                     + "\\nGrade: " + signal.grade\n'
        '                     + "\\nQty: " + str(round(quantity, 6))\n'
        '                     + "  Price: " + str(round(mark_price, 6))\n'
        '                     + "\\nSL: " + str(round(signal.sl_price, 6)))\n'
        '        if signal.tp_price is not None:\n'
        '            entry_msg += "  TP: " + str(round(signal.tp_price, 6))',
    )
    if ok:
        log("  executor.py: ENTRY -- done")

    # --- position_monitor.py: HARD STOP (lines 275-277) ---
    ok = replace_in_file(
        monitor_py,
        'self.notifier.send(\n'
        '                "HARD STOP: daily loss limit ($"\n'
        '                + str(round(abs(current["daily_pnl"]), 2)) + ")")',
        'self.notifier.send(\n'
        '                "<b>HARD STOP</b>\\nDaily loss limit: $"\n'
        '                + str(round(abs(current["daily_pnl"]), 2)))',
    )
    if ok:
        log("  position_monitor.py: HARD STOP -- done")

    # --- position_monitor.py: EXIT (lines 278-282) ---
    ok = replace_in_file(
        monitor_py,
        'msg = ("EXIT: " + key\n'
        '               + " reason=" + exit_reason\n'
        '               + " pnl=" + str(round(pnl_net, 2))\n'
        '               + " daily=" + str(round(\n'
        '                   current.get("daily_pnl", 0), 2)))',
        'msg = ("<b>EXIT</b>  " + key\n'
        '               + "\\nReason: " + exit_reason\n'
        '               + "\\nPnL: $" + str(round(pnl_net, 2))\n'
        '               + "\\nDaily: $" + str(round(\n'
        '                   current.get("daily_pnl", 0), 2)))',
    )
    if ok:
        log("  position_monitor.py: EXIT -- done")

    # --- position_monitor.py: DAILY SUMMARY (lines 298-301) ---
    ok = replace_in_file(
        monitor_py,
        'summary = ("DAILY SUMMARY: pnl="\n'
        '                       + str(round(daily_pnl, 2))\n'
        '                       + " trades=" + str(daily_trades)\n'
        '                       + " open=" + str(open_count))',
        'summary = ("<b>DAILY SUMMARY</b>"\n'
        '                       + "\\nPnL: $" + str(round(daily_pnl, 2))\n'
        '                       + "\\nTrades: " + str(daily_trades)\n'
        '                       + "\\nOpen: " + str(open_count))',
    )
    if ok:
        log("  position_monitor.py: DAILY SUMMARY -- done")

    # --- position_monitor.py: WARNING (lines 322-328) ---
    ok = replace_in_file(
        monitor_py,
        'self.notifier.send(\n'
        '                "WARNING: daily loss at "\n'
        '                + str(round(pct_of_limit, 1))\n'
        '                + "% of limit ($"\n'
        '                + str(round(abs(daily_pnl), 2))\n'
        '                + " / $" + str(round(self.daily_loss_limit, 2))\n'
        '                + ")")',
        'self.notifier.send(\n'
        '                "<b>WARNING</b>\\nDaily loss at "\n'
        '                + str(round(pct_of_limit, 1))\n'
        '                + "% of limit\\n$"\n'
        '                + str(round(abs(daily_pnl), 2))\n'
        '                + " / $" + str(round(self.daily_loss_limit, 2)))',
    )
    if ok:
        log("  position_monitor.py: WARNING -- done")

    # --- main.py: STARTUP (lines 218-221) ---
    ok = replace_in_file(
        main_py,
        'start_msg = ("Bot started: "\n'
        '                 + str(len(symbols)) + " coins, "\n'
        '                 + str(open_count) + " open, "\n'
        '                 + ("DEMO" if demo_mode else "LIVE"))',
        'start_msg = ("<b>BOT STARTED</b>"\n'
        '                 + "\\nCoins: " + str(len(symbols))\n'
        '                 + "\\nOpen: " + str(open_count)\n'
        '                 + "\\nMode: " + ("DEMO" if demo_mode else "LIVE"))',
    )
    if ok:
        log("  main.py: STARTUP -- done")

    # --- main.py: SHUTTING DOWN (line 250) ---
    ok = replace_in_file(
        main_py,
        'notifier.send("Bot shutting down \u2014 waiting for in-flight ops...")',
        'notifier.send("<b>BOT STOPPING</b>\\nWaiting for in-flight ops...")',
    )
    if ok:
        log("  main.py: SHUTTING DOWN -- done")

    # --- main.py: STOPPED (line 256) ---
    ok = replace_in_file(
        main_py,
        'notifier.send("Bot stopped")',
        'notifier.send("<b>BOT STOPPED</b>")',
    )
    if ok:
        log("  main.py: STOPPED -- done")

    MODIFIED.extend(["executor.py", "position_monitor.py", "main.py"])

    # ------------------------------------------------------------------
    # STEP 4: Validate all Python files
    # ------------------------------------------------------------------
    log("")
    log("[STEP 4/4] Validating Python files...")

    validate_py(executor_py)
    validate_py(monitor_py)
    validate_py(main_py)

    # ------------------------------------------------------------------
    # SUMMARY
    # ------------------------------------------------------------------
    log("")
    log("=" * 60)
    if ERRORS:
        log("BUILD RESULT: FAILURES DETECTED")
        log("")
        for err in ERRORS:
            log("  ERROR: " + err)
        log("")
        log("Backups available to restore:")
        for bak in BACKED_UP:
            log("  " + bak)
        sys.exit(1)
    else:
        log("BUILD RESULT: ALL PASSED")
        log("")
        log("Created " + str(len(CREATED)) + " new files:")
        for f in CREATED:
            log("  " + f)
        log("")
        log("Modified " + str(len(MODIFIED)) + " files (backups saved):")
        for f in MODIFIED:
            log("  " + f)
        for bak in BACKED_UP:
            log("  backup: " + bak)
        log("")
        log("NEXT STEPS:")
        log("  1. Test bot manually:")
        log('     powershell -ExecutionPolicy Bypass -File "' + str(SCRIPTS_DIR / "run_bot.ps1") + '"')
        log("  2. Install auto-start (as admin):")
        log('     powershell -ExecutionPolicy Bypass -File "' + str(SCRIPTS_DIR / "install_autostart.ps1") + '"')
    log("=" * 60)


# ============================================================================
# FILE CONTENTS
# ============================================================================

RUN_BOT_PS1_CONTENT = r'''# run_bot.ps1 -- BingX bot wrapper with crash recovery
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
'''

TASK_XML_CONTENT = r'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>BingX Trading Bot - auto-start on boot with crash recovery</Description>
    <Author>S23Web3</Author>
  </RegistrationInfo>
  <Triggers>
    <BootTrigger>
      <Enabled>true</Enabled>
      <Delay>PT60S</Delay>
    </BootTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>true</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <DisallowStartOnRemoteAppSession>false</DisallowStartOnRemoteAppSession>
    <UseUnifiedSchedulingEngine>true</UseUnifiedSchedulingEngine>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>powershell.exe</Command>
      <Arguments>-ExecutionPolicy Bypass -WindowStyle Hidden -File "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\run_bot.ps1"</Arguments>
      <WorkingDirectory>C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
'''

INSTALL_PS1_CONTENT = r'''# install_autostart.ps1 -- Register BingXBot as a scheduled task
# Run as admin: powershell -ExecutionPolicy Bypass -File install_autostart.ps1
# To uninstall: schtasks /delete /tn "BingXBot" /f

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$xmlPath = Join-Path $scriptDir "bingx-bot-task.xml"

# Check admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: Run this script as Administrator."
    Write-Host "  Right-click PowerShell -> Run as administrator"
    Write-Host "  Then: powershell -ExecutionPolicy Bypass -File `"$($MyInvocation.MyCommand.Path)`""
    exit 1
}

# Check XML exists
if (-not (Test-Path $xmlPath)) {
    Write-Host "ERROR: $xmlPath not found."
    Write-Host "  Run the build script first: python scripts\build_autostart_and_tg.py"
    exit 1
}

Write-Host "Registering BingXBot scheduled task..."
schtasks /create /tn "BingXBot" /xml $xmlPath /f

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "SUCCESS: BingXBot task registered."
    Write-Host ""
    Write-Host "  Auto-starts on reboot (60s delay for network)."
    Write-Host "  Start now:    schtasks /run /tn BingXBot"
    Write-Host "  Check status: schtasks /query /tn BingXBot"
    Write-Host "  Stop:         schtasks /end /tn BingXBot"
    Write-Host "  Remove:       schtasks /delete /tn BingXBot /f"
} else {
    Write-Host "FAILED: Could not register task. Check output above."
}
'''


if __name__ == "__main__":
    main()
