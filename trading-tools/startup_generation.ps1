# Four Pillars ML - Qwen Build + Test + Fix Pipeline
# Handles: crashes, restarts, blue screens, power outages
# Flow: Qwen builds code -> test -> if error, Qwen fixes -> retest
# Tracks time per phase
# Double-click START_GENERATION.bat to launch

param(
    [switch]$SkipOllama = $false,
    [switch]$SkipNvitop = $false,
    [switch]$SkipBuild = $false,
    [int]$MaxFixRetries = 3
)

$ErrorActionPreference = "Continue"

$ProjectDir = "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester"
$ToolsDir = "C:\Users\User\Documents\Obsidian Vault\trading-tools"
$Model = "qwen2.5-coder:14b"
$OllamaPath = "C:\Users\User\AppData\Local\Programs\Ollama\ollama.exe"
$MasterPrompt = Join-Path $ToolsDir "QWEN-MASTER-PROMPT-ALL-TASKS.md"
$TimeLog = Join-Path $ProjectDir "scripts\build_times.txt"

# =====================================================================
# TIME TRACKING
# =====================================================================

function Log-Time {
    param([string]$Phase, [string]$Message)
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] [$Phase] $Message"
    Write-Host $line -ForegroundColor Gray
    Add-Content -Path $TimeLog -Value $line -Encoding utf8
}

function Get-ElapsedStr {
    param([datetime]$Start)
    $elapsed = (Get-Date) - $Start
    if ($elapsed.TotalHours -ge 1) {
        return "{0:N1}h" -f $elapsed.TotalHours
    } elseif ($elapsed.TotalMinutes -ge 1) {
        return "{0:N1}m" -f $elapsed.TotalMinutes
    } else {
        return "{0:N0}s" -f $elapsed.TotalSeconds
    }
}

# =====================================================================
# FIX PROMPT -- sent to Qwen when tests fail
# =====================================================================
$FixPrompt = @'
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.

You are a senior Python developer working on the Four Pillars ML trading backtester.

== PROJECT CONTEXT ==

PROJECT DIR: C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester
PYTHON: 3.13 on Windows 11
STACK: pandas, numpy, xgboost, shap, streamlit, plotly, psycopg2

Key column names in signals: stoch_9, stoch_14, stoch_40, stoch_60, atr, cloud3_bull, ema34, ema50
Trade fields: direction, grade, entry_bar, exit_bar, entry_price, exit_price, sl_price, tp_price, pnl, commission, net_pnl, mfe, mae, exit_reason, saw_green, be_raised

== YOUR JOB ==

The test failed. Read the error output below and fix the code.

1. Identify the EXACT file and line number causing the failure
2. Explain the root cause in ONE sentence
3. Output the COMPLETE fixed file -- not a diff, not a snippet, the FULL file

== OUTPUT FORMAT (strict) ==

```python
# relative/path/to/file.py
[entire corrected file contents here]
```

If multiple files need fixing, output one code block per file, each starting with # path/to/file.py.

== RULES ==
- No emojis
- Max 2 sentences of explanation before the code block
- Do NOT add features, do NOT refactor, do NOT change anything unrelated to the error
- Fix ONLY what is broken -- minimal targeted change
- The code block MUST contain the COMPLETE file, not a partial snippet
- The FIRST line inside the python code block MUST be # path/to/file.py

== TEST ERROR OUTPUT FOLLOWS ==

'@

# =====================================================================
# STARTUP BANNER
# =====================================================================

$scriptStart = Get-Date
$testExitCode = -1
$fixAttempt = 0

Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "Four Pillars ML - Qwen Build Pipeline" -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[*] Project:  $ProjectDir" -ForegroundColor Cyan
Write-Host "[*] Model:    $Model" -ForegroundColor Cyan
Write-Host "[*] Tools:    $ToolsDir" -ForegroundColor Cyan
Write-Host "[*] Started:  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host ""

# Init time log
if (-not (Test-Path (Split-Path $TimeLog))) {
    New-Item -ItemType Directory -Path (Split-Path $TimeLog) -Force | Out-Null
}
Add-Content -Path $TimeLog -Value "`n=======================================================" -Encoding utf8
Add-Content -Path $TimeLog -Value "BUILD SESSION -- $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -Encoding utf8
Add-Content -Path $TimeLog -Value "=======================================================" -Encoding utf8

# =====================================================================
# PHASE 0: Start Ollama + nvitop
# =====================================================================

$phase0Start = Get-Date
Log-Time "SETUP" "Phase 0: Starting services"

# 0a. Start Ollama
if (-not $SkipOllama) {
    Write-Host "[0a] Checking Ollama service..." -ForegroundColor Yellow

    $ollamaProcess = Get-Process ollama -ErrorAction SilentlyContinue

    if ($null -eq $ollamaProcess) {
        Write-Host "     Starting Ollama in new terminal..." -ForegroundColor Green
        Start-Process -FilePath "powershell" -ArgumentList "-NoExit -Command `"& '$OllamaPath' serve`""
        Start-Sleep -Seconds 8

        $ollamaProcess = Get-Process ollama -ErrorAction SilentlyContinue
        if ($null -eq $ollamaProcess) {
            Write-Host "     [WARN] Failed to start Ollama -- script cannot continue" -ForegroundColor Red
            Log-Time "SETUP" "FAILED: Ollama did not start"
            exit 1
        } else {
            Write-Host "     [OK] Ollama started (PID: $($ollamaProcess.Id))" -ForegroundColor Green
        }
    } else {
        Write-Host "     [OK] Ollama already running (PID: $($ollamaProcess.Id))" -ForegroundColor Green
    }
    Write-Host ""
}

# 0b. Check Qwen model
Write-Host "[0b] Checking Qwen model..." -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 15

    $qwenLoaded = $response.models | Where-Object { $_.name -like "$Model*" }

    if ($null -eq $qwenLoaded) {
        Write-Host "     [WARN] $Model not found, pulling..." -ForegroundColor Yellow
        & $OllamaPath pull $Model 2>&1
        Write-Host "     [OK] Model pulled" -ForegroundColor Green
    } else {
        Write-Host "     [OK] Qwen model ready: $Model" -ForegroundColor Green
    }
} catch {
    Write-Host "     [WARN] Could not verify Qwen model -- waiting 10s and retrying" -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 15
        Write-Host "     [OK] Ollama API responding" -ForegroundColor Green
    } catch {
        Write-Host "     [FAIL] Ollama API not responding -- cannot continue" -ForegroundColor Red
        Log-Time "SETUP" "FAILED: Ollama API unreachable"
        exit 1
    }
}

Write-Host ""

# 0c. Start nvitop
if (-not $SkipNvitop) {
    Write-Host "[0c] Starting GPU monitor (nvitop)..." -ForegroundColor Yellow

    $nvitopProcess = Get-Process nvitop -ErrorAction SilentlyContinue

    if ($null -eq $nvitopProcess) {
        Start-Process -FilePath "powershell" -ArgumentList "-NoExit -Command nvitop" -WindowStyle Normal
        Write-Host "     [OK] nvitop started in new window" -ForegroundColor Green
    } else {
        Write-Host "     [OK] nvitop already running" -ForegroundColor Green
    }
    Write-Host ""
}

Log-Time "SETUP" "Phase 0 complete ($(Get-ElapsedStr $phase0Start))"
Write-Host ""

# =====================================================================
# PHASE 1: BUILD -- Qwen generates code via auto_generate_files.py
# =====================================================================

$phase1Start = Get-Date
Log-Time "BUILD" "Phase 1: Qwen code generation starting"

Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "[PHASE 1] QWEN CODE GENERATION" -ForegroundColor Yellow
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Prompt:  $MasterPrompt" -ForegroundColor Cyan
Write-Host "Output:  $ProjectDir" -ForegroundColor Cyan
Write-Host ""

$checkpointFile = Join-Path $ToolsDir "generation_checkpoint.txt"
$generatorScript = Join-Path $ToolsDir "auto_generate_files.py"

if ($SkipBuild) {
    Write-Host "[SKIP] Build phase skipped via -SkipBuild flag" -ForegroundColor Yellow
    Log-Time "BUILD" "SKIPPED by flag"
} elseif (Test-Path $checkpointFile) {
    # Resume from checkpoint
    $cpSize = (Get-Item $checkpointFile).Length
    Write-Host "[RESUME] Checkpoint found ($cpSize bytes) -- resuming generation" -ForegroundColor Green
    Write-Host ""

    Set-Location $ToolsDir
    python $generatorScript $MasterPrompt --resume 2>&1 | Tee-Object -Variable buildOutput
    $buildExitCode = $LASTEXITCODE

    if ($buildExitCode -eq 0) {
        Write-Host ""
        Write-Host "[OK] Code generation complete (resumed)" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "[WARN] Code generation exited with code $buildExitCode" -ForegroundColor Yellow
    }

    Log-Time "BUILD" "Phase 1 complete (resumed, $(Get-ElapsedStr $phase1Start))"
} else {
    # Fresh build
    Write-Host "[START] Sending master prompt to Qwen..." -ForegroundColor Green
    Write-Host "        This may take hours. Output streams live below." -ForegroundColor Gray
    Write-Host ""

    Set-Location $ToolsDir
    python $generatorScript $MasterPrompt 2>&1 | Tee-Object -Variable buildOutput
    $buildExitCode = $LASTEXITCODE

    if ($buildExitCode -eq 0) {
        Write-Host ""
        Write-Host "[OK] Code generation complete" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "[WARN] Code generation exited with code $buildExitCode" -ForegroundColor Yellow
    }

    Log-Time "BUILD" "Phase 1 complete (fresh, $(Get-ElapsedStr $phase1Start))"
}

Write-Host ""

# =====================================================================
# PHASE 2: TEST -- run test_ml_pipeline.py
# =====================================================================

$phase2Start = Get-Date
Log-Time "TEST" "Phase 2: Testing ML pipeline"

Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "[PHASE 2] TEST ML PIPELINE" -ForegroundColor Yellow
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $ProjectDir

$testScript = Join-Path $ProjectDir "scripts\test_ml_pipeline.py"

if (-not (Test-Path $testScript)) {
    Write-Host "[WARN] test_ml_pipeline.py not found -- skipping tests" -ForegroundColor Yellow
    Log-Time "TEST" "SKIPPED: test script not found"
} else {
    python $testScript 2>&1 | Tee-Object -Variable testOutput
    $testExitCode = $LASTEXITCODE

    if ($testExitCode -eq 0) {
        Write-Host ""
        Write-Host "=======================================================" -ForegroundColor Green
        Write-Host "[PASS] All ML pipeline tests passed!" -ForegroundColor Green
        Write-Host "=======================================================" -ForegroundColor Green
        Log-Time "TEST" "Phase 2 PASSED ($(Get-ElapsedStr $phase2Start))"
    } else {
        Write-Host ""
        Write-Host "=======================================================" -ForegroundColor Red
        Write-Host "[FAIL] ML pipeline tests failed (exit code: $testExitCode)" -ForegroundColor Red
        Write-Host "=======================================================" -ForegroundColor Red
        Log-Time "TEST" "Phase 2 FAILED ($(Get-ElapsedStr $phase2Start))"

        # Save error output
        $errorLogFile = Join-Path $ProjectDir "scripts\last_test_error.txt"
        ($testOutput -join "`n") | Out-File -FilePath $errorLogFile -Encoding utf8

        # =====================================================================
        # PHASE 3: FIX -- feed errors to Qwen, apply fixes, retest
        # =====================================================================

        $fixAttempt = 0

        while ($fixAttempt -lt $MaxFixRetries -and $testExitCode -ne 0) {
            $fixAttempt++
            $phase3Start = Get-Date
            Log-Time "FIX" "Phase 3: Fix attempt $fixAttempt of $MaxFixRetries"

            Write-Host ""
            Write-Host "-------------------------------------------------------" -ForegroundColor Yellow
            Write-Host "[FIX] Attempt $fixAttempt of $MaxFixRetries -- sending error to Qwen" -ForegroundColor Yellow
            Write-Host "-------------------------------------------------------" -ForegroundColor Yellow
            Write-Host ""

            # Trim test output to last 200 lines
            $errorLines = $testOutput
            if ($errorLines.Count -gt 200) {
                $errorLines = $errorLines[-200..-1]
            }
            $trimmedError = $errorLines -join "`n"

            # Build the fix prompt
            $fullFixPrompt = @"
$FixPrompt

$trimmedError
"@

            # Send to Qwen via Ollama CLI
            try {
                $qwenFixStart = Get-Date
                $qwenResponse = $fullFixPrompt | & $OllamaPath run $Model 2>&1
                $qwenText = $qwenResponse -join "`n"
                $qwenElapsed = Get-ElapsedStr $qwenFixStart

                # Save response
                $fixFile = Join-Path $ProjectDir "scripts\qwen_fix_attempt_$fixAttempt.txt"
                $qwenText | Out-File -FilePath $fixFile -Encoding utf8

                Write-Host "[QWEN] Response saved ($qwenElapsed): scripts\qwen_fix_attempt_$fixAttempt.txt" -ForegroundColor Yellow
                Write-Host ""
                Write-Host $qwenText
                Write-Host ""

                Log-Time "FIX" "Qwen responded in $qwenElapsed"

                # Try to apply code fixes
                if ($qwenText -match '```python') {
                    Write-Host "[FIX] Code fix detected. Extracting and applying..." -ForegroundColor Green

                    # Inline Python to extract and apply fixes
                    $applyScript = @'
import re, sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(encoding="utf-8")
project = Path(sys.argv[2])
blocks = re.findall(r'```python\s*\n(.*?)```', text, re.DOTALL)
applied = 0
for block in blocks:
    lines = block.strip().split("\n")
    m = re.match(r'^#\s*(.+\.py)\s*$', lines[0])
    if m:
        rel_path = m.group(1).strip()
        code = "\n".join(lines[1:])
        target = project / rel_path
        if target.exists():
            target.write_text(code, encoding="utf-8")
            print(f"  APPLIED: {rel_path} ({len(code)} bytes)")
            applied += 1
        else:
            # Also try with ml/ prefix if bare filename
            if "/" not in rel_path and "\\" not in rel_path:
                for subdir in ["ml", "scripts", "engine", "signals", "data", "optimizer"]:
                    alt = project / subdir / rel_path
                    if alt.exists():
                        alt.write_text(code, encoding="utf-8")
                        print(f"  APPLIED: {subdir}/{rel_path} ({len(code)} bytes)")
                        applied += 1
                        break
                else:
                    print(f"  SKIP: {rel_path} (file not found)")
            else:
                print(f"  SKIP: {rel_path} (file does not exist)")
    else:
        print(f"  SKIP: code block has no file path header")
print(f"Applied {applied} fix(es)")
sys.exit(0 if applied > 0 else 1)
'@

                    $applyScriptFile = Join-Path $ProjectDir "scripts\_apply_qwen_fix.py"
                    $applyScript | Out-File -FilePath $applyScriptFile -Encoding utf8

                    python $applyScriptFile $fixFile $ProjectDir 2>&1
                    $applyExitCode = $LASTEXITCODE

                    if ($applyExitCode -eq 0) {
                        Write-Host "[FIX] Fix applied. Re-running tests..." -ForegroundColor Green
                        Log-Time "FIX" "Fix applied, retesting"
                    } else {
                        Write-Host "[FIX] No applicable fixes found." -ForegroundColor Yellow
                        Log-Time "FIX" "No applicable fixes in Qwen response"
                    }
                } else {
                    Write-Host "[FIX] No code block in Qwen response. Diagnosis only." -ForegroundColor Yellow
                    Log-Time "FIX" "Qwen gave diagnosis only, no code"
                }

                # Re-run tests
                Write-Host ""
                Write-Host "[RETEST] Running test_ml_pipeline.py..." -ForegroundColor Cyan
                python $testScript 2>&1 | Tee-Object -Variable testOutput
                $testExitCode = $LASTEXITCODE

                if ($testExitCode -eq 0) {
                    Write-Host ""
                    Write-Host "=======================================================" -ForegroundColor Green
                    Write-Host "[PASS] Tests passed after fix attempt $fixAttempt!" -ForegroundColor Green
                    Write-Host "=======================================================" -ForegroundColor Green
                    Log-Time "FIX" "Phase 3 PASSED on attempt $fixAttempt ($(Get-ElapsedStr $phase3Start))"
                } else {
                    Write-Host ""
                    Write-Host "[FAIL] Tests still failing after fix attempt $fixAttempt" -ForegroundColor Red
                    ($testOutput -join "`n") | Out-File -FilePath $errorLogFile -Encoding utf8
                    Log-Time "FIX" "Fix attempt $fixAttempt FAILED ($(Get-ElapsedStr $phase3Start))"
                }

            } catch {
                Write-Host "[FIX] Failed to get Qwen response: $_" -ForegroundColor Red
                Log-Time "FIX" "Qwen API error: $_"
            }

            if ($testExitCode -ne 0 -and $fixAttempt -lt $MaxFixRetries) {
                Write-Host ""
                Write-Host "Retrying fix in 5 seconds..." -ForegroundColor Cyan
                Start-Sleep -Seconds 5
            }
        }
    }
}

# =====================================================================
# FINAL SUMMARY
# =====================================================================

$totalElapsed = Get-ElapsedStr $scriptStart

Write-Host ""
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "BUILD SESSION COMPLETE" -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Total time:  $totalElapsed" -ForegroundColor White
Write-Host "Time log:    scripts\build_times.txt" -ForegroundColor White
Write-Host ""

Log-Time "DONE" "Session complete ($totalElapsed)"

if ($testExitCode -eq 0) {
    Write-Host "STATUS: ALL TESTS PASSED" -ForegroundColor Green
    Write-Host ""
    Write-Host "Ready for tomorrow:" -ForegroundColor Cyan
    Write-Host "  - Review generated files in $ProjectDir" -ForegroundColor White
    Write-Host "  - Run dashboard: streamlit run scripts\dashboard.py" -ForegroundColor White
    Write-Host "  - Check time log: scripts\build_times.txt" -ForegroundColor White
    Log-Time "DONE" "STATUS: PASSED"
} else {
    Write-Host "STATUS: TESTS STILL FAILING" -ForegroundColor Red
    Write-Host ""
    Write-Host "Files to review tomorrow:" -ForegroundColor Yellow
    Write-Host "  scripts\build_times.txt           -- time per phase" -ForegroundColor White
    Write-Host "  scripts\last_test_error.txt        -- last test error" -ForegroundColor White
    for ($i = 1; $i -le $fixAttempt; $i++) {
        $f = "scripts\qwen_fix_attempt_$i.txt"
        if (Test-Path (Join-Path $ProjectDir $f)) {
            Write-Host "  $f  -- Qwen fix #$i" -ForegroundColor White
        }
    }
    Log-Time "DONE" "STATUS: FAILED after $fixAttempt fix attempts"
}

Write-Host ""
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "Window stays open -- scroll up to review output" -ForegroundColor Yellow
Write-Host "Press Ctrl+C or close window to exit" -ForegroundColor Gray
Write-Host "=======================================================" -ForegroundColor Cyan
