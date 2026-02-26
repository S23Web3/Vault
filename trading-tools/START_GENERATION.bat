@echo off
REM Four Pillars ML - Qwen Build Pipeline
REM Flow: Qwen generates code -> test -> fix errors -> report
REM Time tracked per phase in scripts\build_times.txt

echo.
echo ============================================================
echo Four Pillars ML - Qwen Build Pipeline
echo ============================================================
echo.
echo Phase 1: Qwen generates code from master prompt
echo Phase 2: Run ML pipeline tests
echo Phase 3: If errors, Qwen fixes and retests
echo.

cd /d "C:\Users\User\Documents\Obsidian Vault\trading-tools"
powershell.exe -NoExit -ExecutionPolicy Bypass -File "startup_generation.ps1"
