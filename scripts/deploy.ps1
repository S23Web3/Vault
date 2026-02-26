# ============================================================================
# deploy.ps1 -- Push vault changes + deploy to VPS (run on PC in PowerShell)
# ============================================================================
# Date:    2026-02-26
# Purpose: Push local vault changes to GitHub, optionally sync to VPS
#          and/or restart the bot.
#
# Usage (5 modes):
#
#   1. Push only (backup to GitHub, VPS untouched):
#      .\scripts\deploy.ps1 -Message "added session log"
#
#   2. Push + sync VPS files (git pull only, bot keeps running):
#      .\scripts\deploy.ps1 -Message "updated strategy docs" -Sync
#
#   3. Push + sync + restart bot (use ONLY when bot code changed):
#      .\scripts\deploy.ps1 -Message "fixed commission rate" -Restart
#      WARNING: Restarting kills 16.7h of warmup. Only use for bot code changes.
#
#   4. Check bot status on VPS:
#      .\scripts\deploy.ps1 -Status
#
#   5. View bot logs:
#      .\scripts\deploy.ps1 -Logs
#
#   6. Rollback VPS to a previous commit:
#      .\scripts\deploy.ps1 -Rollback
#      (shows recent commits on VPS, you pick one)
#
# Parameters:
#   -Message   Commit message (required for push)
#   -Sync      After pushing, git pull on VPS (NO bot restart)
#   -Restart   After pushing, git pull on VPS AND restart bot
#   -Status    Just check bot status on VPS
#   -Logs      Show last 50 lines of bot logs from VPS
#   -Rollback  Show VPS commit history, roll back to chosen commit
# ============================================================================

param(
    [string]$Message,
    [switch]$Sync,
    [switch]$Restart,
    [switch]$Status,
    [switch]$Logs,
    [switch]$Rollback
)

$VAULT = "C:\Users\User\Documents\Obsidian Vault"
$VPS = "root@76.13.20.191"
$SERVICE = "bingx-bot"

# --------------------------------------------------------------------------
# Mode: Status check
# --------------------------------------------------------------------------
if ($Status) {
    Write-Host ""
    Write-Host "--- status $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ---" -ForegroundColor Cyan
    ssh $VPS "systemctl status $SERVICE"
    exit 0
}

# --------------------------------------------------------------------------
# Mode: View logs
# --------------------------------------------------------------------------
if ($Logs) {
    Write-Host ""
    Write-Host "--- logs $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ---" -ForegroundColor Cyan
    ssh $VPS "journalctl -u $SERVICE --no-pager -n 50"
    exit 0
}

# --------------------------------------------------------------------------
# Mode: Rollback
# --------------------------------------------------------------------------
# Shows the last 10 commits on VPS, lets you pick one to roll back to.
# Does NOT touch your PC repo -- only the VPS copy.
# --------------------------------------------------------------------------
if ($Rollback) {
    Write-Host ""
    Write-Host "--- rollback $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ---" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Last 10 commits on VPS:" -ForegroundColor Yellow
    ssh $VPS "cd /root/vault && git log --oneline -10"
    Write-Host ""
    $hash = Read-Host "  Enter commit hash to roll back to (or Ctrl+C to cancel)"
    if ($hash) {
        Write-Host "  Rolling back VPS to $hash..." -ForegroundColor Yellow
        ssh $VPS "cd /root/vault && git checkout $hash -- . && systemctl restart $SERVICE"
        Start-Sleep -Seconds 3
        Write-Host "  Bot status:" -ForegroundColor Cyan
        ssh $VPS "systemctl is-active $SERVICE"
        Write-Host ""
        Write-Host "  Rolled back. To undo: .\scripts\deploy.ps1 -Sync" -ForegroundColor Green
    }
    exit 0
}

# --------------------------------------------------------------------------
# Mode: Push (and optionally sync/restart)
# --------------------------------------------------------------------------
if (-not $Message) {
    Write-Host ""
    Write-Host "ERROR: -Message is required for push." -ForegroundColor Red
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host '  .\scripts\deploy.ps1 -Message "what changed"              # push only' -ForegroundColor White
    Write-Host '  .\scripts\deploy.ps1 -Message "what changed" -Sync        # push + sync VPS files' -ForegroundColor White
    Write-Host '  .\scripts\deploy.ps1 -Message "what changed" -Restart     # push + sync + restart bot' -ForegroundColor White
    Write-Host '  .\scripts\deploy.ps1 -Status                              # check bot' -ForegroundColor White
    Write-Host '  .\scripts\deploy.ps1 -Logs                                # view bot logs' -ForegroundColor White
    Write-Host '  .\scripts\deploy.ps1 -Rollback                            # roll back VPS' -ForegroundColor White
    exit 1
}

Set-Location $VAULT

Write-Host ""
Write-Host "--- deploy $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ---" -ForegroundColor Cyan
Write-Host ""

# Stage all changes
Write-Host "[1/3] Staging changes..." -ForegroundColor Yellow
git add .

# Show what changed
$changes = git diff --cached --stat
if (-not $changes) {
    Write-Host "  No changes to commit." -ForegroundColor DarkGray
    exit 0
}
Write-Host $changes
Write-Host ""

# Safety check: look for things that should NOT be staged
$stagedFiles = git diff --cached --name-only
$dangerous = $stagedFiles | Where-Object {
    $_ -match "\.env$" -or
    $_ -match "\.csv$" -or
    $_ -match "\.parquet$" -or
    $_ -match "__pycache__" -or
    $_ -match "Tv\.md$"
}

if ($dangerous) {
    Write-Host "  WARNING: These files should NOT be committed:" -ForegroundColor Red
    $dangerous | ForEach-Object { Write-Host "    $_" -ForegroundColor Red }
    Write-Host ""
    Write-Host "  Unstaging and aborting. Fix .gitignore." -ForegroundColor Red
    git reset HEAD -- . > $null 2>&1
    exit 1
}

# Commit
Write-Host "[2/3] Committing: $Message" -ForegroundColor Yellow
git commit -m "sync: $Message"
Write-Host ""

# Push
Write-Host "[3/3] Pushing to GitHub..." -ForegroundColor Yellow
git push
Write-Host ""
Write-Host "  Pushed to https://github.com/S23Web3/Vault" -ForegroundColor Green

# --------------------------------------------------------------------------
# Optional: Sync VPS (git pull only, no restart)
# --------------------------------------------------------------------------
if ($Sync -or $Restart) {
    Write-Host ""
    Write-Host "  Syncing VPS files (git pull)..." -ForegroundColor Yellow

    $pullResult = ssh $VPS "cd /root/vault && git pull --ff-only 2>&1" 2>&1
    $pullExitCode = $LASTEXITCODE

    if ($pullExitCode -ne 0) {
        Write-Host ""
        Write-Host "  SSH or git pull FAILED." -ForegroundColor Red
        Write-Host "  Your code is safe on GitHub. The VPS just didn't get it yet." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  To fix, SSH in manually:" -ForegroundColor Yellow
        Write-Host "    ssh $VPS" -ForegroundColor White
        Write-Host "    cd /root/vault" -ForegroundColor White
        Write-Host ""
        Write-Host "  If ff-only failed (conflict):" -ForegroundColor Yellow
        Write-Host "    git stash        # saves VPS-only changes" -ForegroundColor White
        Write-Host "    git pull          # pulls your push" -ForegroundColor White
        Write-Host "    git stash pop     # re-applies VPS changes (if any)" -ForegroundColor White
        Write-Host ""
        Write-Host "  If SSH itself failed (VPS down/network):" -ForegroundColor Yellow
        Write-Host "    Just re-run with -Sync later when VPS is reachable." -ForegroundColor White
        exit 1
    }

    Write-Host "  $pullResult" -ForegroundColor Green
}

# --------------------------------------------------------------------------
# Optional: Restart bot (only with -Restart flag)
# --------------------------------------------------------------------------
# WARNING: Restarting the bot kills the warmup buffer (201 bars = 16.7 hours
# on 5m timeframe). Only use -Restart when actual bot code changed
# (main.py, signal_engine.py, executor.py, etc.).
# For markdown, docs, or strategy notes -- use -Sync instead.
# --------------------------------------------------------------------------
if ($Restart) {
    Write-Host ""
    Write-Host "  *** WARNING: Restarting bot kills 16.7h warmup buffer ***" -ForegroundColor Red
    Write-Host "  Only do this if bot Python code changed." -ForegroundColor Red
    Write-Host "  For docs/notes changes, Ctrl+C now and use -Sync instead." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "  Press ENTER to restart bot, or Ctrl+C to keep it running"

    ssh $VPS "systemctl restart $SERVICE"
    Start-Sleep -Seconds 3
    Write-Host ""
    Write-Host "  Bot status:" -ForegroundColor Cyan
    ssh $VPS "systemctl is-active $SERVICE"
    Write-Host ""
    Write-Host "  Bot restarted. Warmup begins now (~16.7h to full buffer)." -ForegroundColor Yellow
}

Write-Host ""
