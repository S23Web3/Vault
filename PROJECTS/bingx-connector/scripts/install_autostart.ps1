# install_autostart.ps1 -- Register BingXBot as a scheduled task
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
