# VERIFICATION SCRIPT — Test Auto-Start Configuration
# Run this before leaving your desk

Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "AUTO-START VERIFICATION" -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host ""

$allGood = $true

# 1. Check startup shortcut
$startupPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\QwenGeneration.lnk"
if (Test-Path $startupPath) {
    Write-Host "[OK] Startup shortcut exists" -ForegroundColor Green
    Write-Host "    Path: $startupPath" -ForegroundColor Gray
} else {
    Write-Host "[FAIL] Startup shortcut NOT found" -ForegroundColor Red
    $allGood = $false
}

# 2. Check Ollama path fix
$scriptPath = "C:\Users\User\Documents\Obsidian Vault\trading-tools\startup_generation.ps1"
$scriptContent = Get-Content $scriptPath -Raw
if ($scriptContent -match 'ollamaPath.*Programs\\Ollama\\ollama\.exe') {
    Write-Host "[OK] Ollama path fixed in startup script" -ForegroundColor Green
} else {
    Write-Host "[FAIL] Ollama path NOT fixed" -ForegroundColor Red
    $allGood = $false
}

# 3. Check Ollama is installed
$ollamaExe = "C:\Users\User\AppData\Local\Programs\Ollama\ollama.exe"
if (Test-Path $ollamaExe) {
    Write-Host "[OK] Ollama installed at: $ollamaExe" -ForegroundColor Green
} else {
    Write-Host "[FAIL] Ollama NOT found at: $ollamaExe" -ForegroundColor Red
    $allGood = $false
}

# 4. Check if Ollama is running
$ollamaProcess = Get-Process ollama -ErrorAction SilentlyContinue
if ($ollamaProcess) {
    Write-Host "[OK] Ollama is currently running (PID: $($ollamaProcess.Id))" -ForegroundColor Green
} else {
    Write-Host "[WARN] Ollama not running (will auto-start on reboot)" -ForegroundColor Yellow
}

# 5. Check Qwen model
try {
    $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 5 -ErrorAction Stop
    $qwenModel = $response.models | Where-Object { $_.name -like "qwen3-coder:30b*" }
    if ($qwenModel) {
        Write-Host "[OK] Qwen model ready: qwen3-coder:30b" -ForegroundColor Green
    } else {
        Write-Host "[WARN] Qwen model not found (will auto-pull on first run)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[WARN] Could not check Qwen model (Ollama not running)" -ForegroundColor Yellow
}

# 6. Check checkpoint file
$checkpointFile = "C:\Users\User\Documents\Obsidian Vault\trading-tools\generation_checkpoint.txt"
if (Test-Path $checkpointFile) {
    $checkpointSize = (Get-Item $checkpointFile).Length
    Write-Host "[OK] Checkpoint exists: $checkpointSize bytes" -ForegroundColor Green
    Write-Host "    Will resume from this checkpoint on reboot" -ForegroundColor Gray
} else {
    Write-Host "[OK] No checkpoint (will start fresh on reboot)" -ForegroundColor Green
}

# 7. Check auto-login
try {
    $autoLogin = Get-ItemProperty -Path "HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Winlogon" -Name AutoAdminLogon -ErrorAction SilentlyContinue
    if ($autoLogin.AutoAdminLogon -eq "1") {
        Write-Host "[OK] Auto-login is ENABLED" -ForegroundColor Green
    } else {
        Write-Host "[WARN] Auto-login is DISABLED" -ForegroundColor Yellow
        Write-Host "    Run 'netplwiz' to enable auto-login" -ForegroundColor Gray
        Write-Host "    Uncheck: 'Users must enter a user name and password'" -ForegroundColor Gray
    }
} catch {
    Write-Host "[WARN] Could not check auto-login status" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=======================================================" -ForegroundColor Cyan

if ($allGood) {
    Write-Host "[SUCCESS] ALL CHECKS PASSED" -ForegroundColor Green
    Write-Host ""
    Write-Host "What happens on reboot:" -ForegroundColor Cyan
    Write-Host "  1. Windows auto-logs in" -ForegroundColor Gray
    Write-Host "  2. Startup folder runs START_GENERATION.bat" -ForegroundColor Gray
    Write-Host "  3. Ollama starts (if not running)" -ForegroundColor Gray
    Write-Host "  4. Qwen model loads" -ForegroundColor Gray
    Write-Host "  5. Python script resumes from checkpoint" -ForegroundColor Gray
    Write-Host "  6. Code generation continues" -ForegroundColor Gray
    Write-Host ""
    Write-Host "You can now:" -ForegroundColor Green
    Write-Host "  - Leave your desk" -ForegroundColor Green
    Write-Host "  - Reboot anytime" -ForegroundColor Green
    Write-Host "  - Let it run overnight" -ForegroundColor Green
    Write-Host "  - Resume after power cut" -ForegroundColor Green
} else {
    Write-Host "[FAIL] SOME CHECKS FAILED - FIX REQUIRED" -ForegroundColor Red
}

Write-Host "=======================================================" -ForegroundColor Cyan
