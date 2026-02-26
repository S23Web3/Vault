# PowerShell Script to Run Ollama with File Input
# Usage: .\run_ollama_task.ps1

param(
    [string]$TaskFile = "QWEN-MASTER-PROMPT-ALL-TASKS.md",
    [string]$Model = "qwen3-coder:30b"
)

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "Ollama Task Runner" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

# Check if file exists
$FilePath = Join-Path $PSScriptRoot $TaskFile
if (-Not (Test-Path $FilePath)) {
    Write-Host "ERROR: File not found: $FilePath" -ForegroundColor Red
    Write-Host ""
    Write-Host "Available task files:" -ForegroundColor Yellow
    Get-ChildItem $PSScriptRoot -Filter "QWEN-*.md" | ForEach-Object { Write-Host "  - $($_.Name)" }
    exit 1
}

Write-Host "Task file: $TaskFile" -ForegroundColor Green
Write-Host "Model: $Model" -ForegroundColor Green
Write-Host ""

# Read file content
try {
    $Content = Get-Content -Path $FilePath -Raw -Encoding UTF8
    $ContentLength = $Content.Length
    Write-Host "Loaded $ContentLength characters from file" -ForegroundColor Green
}
catch {
    Write-Host "ERROR reading file: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Starting Ollama generation..." -ForegroundColor Cyan
Write-Host "This may take 24-48 hours. Press Ctrl+C to stop." -ForegroundColor Yellow
Write-Host ""
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

# Pass content to Ollama via stdin
try {
    $Content | ollama run $Model
}
catch {
    Write-Host ""
    Write-Host "ERROR: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "Generation complete!" -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Cyan
