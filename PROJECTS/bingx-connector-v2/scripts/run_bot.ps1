# run_bot.ps1 -- BingX bot wrapper with crash recovery
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
