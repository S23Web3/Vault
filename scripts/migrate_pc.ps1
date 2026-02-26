# ============================================================================
# migrate_pc.ps1 -- Vault to GitHub Migration (run on PC in PowerShell)
# ============================================================================
# Date:    2026-02-26
# Purpose: Initialize the Obsidian Vault as a git repo, create .gitignore,
#          commit everything (minus heavy data), push to S23Web3/Vault (private).
#
# Prerequisites:
#   - Git installed and on PATH
#   - Repo S23Web3/Vault already created on GitHub (private)
#   - SSH key for GitHub (script will help you set one up if missing)
#
# Usage:
#   Open PowerShell, then:
#   cd "C:\Users\User\Documents\Obsidian Vault"
#   .\scripts\migrate_pc.ps1
#
# What this script does (step by step):
#   0. Checks git is installed, checks/sets up SSH key for GitHub
#   1. Removes the backtester's standalone .git (flat inclusion into vault repo)
#   2. Initializes a new git repo at the vault root
#   3. Creates .gitignore to exclude heavy data, secrets, and artifacts
#   4. Stages all files, shows summary for review
#   5. Commits (with pause for your review)
#   6. Adds GitHub remote and pushes
#
# What this script does NOT do:
#   - It does NOT delete any of your files
#   - It does NOT touch the VPS
#   - It does NOT run the bot
#
# Every step pauses so you can see what happened before moving on.
# Press Ctrl+C at any pause to abort safely.
# ============================================================================

# We do NOT use $ErrorActionPreference = "Stop" globally because SSH returns
# non-zero on success ("successfully authenticated" comes via stderr exit 1).
# Instead, each step handles its own errors explicitly.

$VAULT = "C:\Users\User\Documents\Obsidian Vault"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Vault Migration Script -- Part A (PC)"   -ForegroundColor Cyan
Write-Host " $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ==========================================================================
# PRE-CHECK 1/3: Git installed
# ==========================================================================

Write-Host "[Pre-check 1/3] Checking git..." -ForegroundColor Yellow

$gitVer = $null
try {
    $gitVer = git --version 2>&1
} catch {}

if ($gitVer -and $gitVer -match "git version") {
    Write-Host "  PASS: $gitVer" -ForegroundColor Green
} else {
    Write-Host "  FAIL: git not found on PATH." -ForegroundColor Red
    Write-Host ""
    Write-Host "  Install Git for Windows: https://git-scm.com/download/win" -ForegroundColor Yellow
    Write-Host "  After installing, restart PowerShell and re-run this script." -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# ==========================================================================
# PRE-CHECK 2/3: Git user identity
# ==========================================================================
# git commit requires user.name and user.email. If not set, commit will
# fail with "Please tell me who you are". We check and set if needed.
# ==========================================================================

Write-Host "[Pre-check 2/3] Checking git user identity..." -ForegroundColor Yellow

$gitUserName = $null
$gitUserEmail = $null
try { $gitUserName = git config --global user.name 2>&1 } catch {}
try { $gitUserEmail = git config --global user.email 2>&1 } catch {}

if ($gitUserName -and $gitUserEmail -and $gitUserName -notmatch "fatal") {
    Write-Host "  PASS: user.name  = $gitUserName" -ForegroundColor Green
    Write-Host "  PASS: user.email = $gitUserEmail" -ForegroundColor Green
} else {
    Write-Host "  Git user identity not set. Setting it now..." -ForegroundColor Yellow
    Write-Host "  WHY: git commit needs a name and email to tag commits." -ForegroundColor DarkGray
    Write-Host ""
    git config --global user.name "S23Web3"
    git config --global user.email "malik@shortcut23.com"
    Write-Host "  SET: user.name  = S23Web3" -ForegroundColor Green
    Write-Host "  SET: user.email = malik@shortcut23.com" -ForegroundColor Green
}

Write-Host ""

# ==========================================================================
# PRE-CHECK 3/3: SSH key for GitHub
# ==========================================================================
# GitHub needs an SSH key to push/pull over git@github.com.
# ssh -T git@github.com returns exit code 1 even on SUCCESS (it prints
# "successfully authenticated" to stderr). PowerShell treats this as an
# error if $ErrorActionPreference = "Stop", so we catch it carefully.
#
# If no key exists: we generate one, show it, pause for you to add it.
# If key exists but GitHub rejects it: show the public key, pause.
# If already working: skip ahead.
# ==========================================================================

Write-Host "[Pre-check 3/3] Checking SSH key for GitHub..." -ForegroundColor Yellow
Write-Host ""

$sshKeyPath = "$env:USERPROFILE\.ssh\id_ed25519"
$sshPubPath = "$env:USERPROFILE\.ssh\id_ed25519.pub"

# Test current GitHub connection (suppress errors -- ssh always exits non-zero)
$sshResult = ssh -T git@github.com 2>&1 | Out-String

if ($sshResult -match "successfully authenticated") {
    Write-Host "  PASS: GitHub SSH already working." -ForegroundColor Green
    Write-Host "  $($sshResult.Trim())" -ForegroundColor DarkGray
    Write-Host ""
} else {
    # SSH didn't work. Check if we even have a key.
    if (Test-Path $sshKeyPath) {
        Write-Host "  SSH key exists at: $sshKeyPath" -ForegroundColor Yellow
        Write-Host "  But GitHub doesn't recognize it yet." -ForegroundColor Yellow
    } else {
        Write-Host "  No SSH key found. Generating one now..." -ForegroundColor Yellow
        Write-Host ""

        # Create .ssh dir if missing
        $sshDir = "$env:USERPROFILE\.ssh"
        if (-not (Test-Path $sshDir)) {
            New-Item -ItemType Directory -Path $sshDir -Force | Out-Null
        }

        # Generate key with empty passphrase.
        # PowerShell quirk: '""' passes literal empty to native commands on PS 5.1.
        # We pipe empty input as a safer cross-version approach.
        Write-Output "y" | ssh-keygen -t ed25519 -C "malik@shortcut23.com" -f $sshKeyPath -N "" 2>&1 | Out-Null

        if (Test-Path $sshPubPath) {
            Write-Host "  DONE: Key generated at $sshKeyPath" -ForegroundColor Green
        } else {
            Write-Host "  FAIL: ssh-keygen did not create a key." -ForegroundColor Red
            Write-Host "  Try running manually:" -ForegroundColor Yellow
            Write-Host "    ssh-keygen -t ed25519 -C `"malik@shortcut23.com`"" -ForegroundColor White
            Write-Host "  Press Enter for all prompts (no passphrase)." -ForegroundColor White
            Write-Host "  Then re-run this script." -ForegroundColor Yellow
            exit 1
        }
    }

    # Show the public key
    Write-Host ""
    Write-Host "  ============================================" -ForegroundColor Cyan
    Write-Host "  YOUR PUBLIC KEY (copy everything below):" -ForegroundColor Cyan
    Write-Host "  ============================================" -ForegroundColor Cyan
    Write-Host ""
    $pubKey = Get-Content $sshPubPath
    Write-Host "  $pubKey" -ForegroundColor White
    Write-Host ""
    Write-Host "  ============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  WHAT TO DO:" -ForegroundColor Yellow
    Write-Host "    1. Copy the key above" -ForegroundColor White
    Write-Host "    2. Go to: https://github.com/settings/keys" -ForegroundColor White
    Write-Host "    3. Click 'New SSH key'" -ForegroundColor White
    Write-Host "    4. Title: 'Obsidian Vault PC'" -ForegroundColor White
    Write-Host "    5. Paste the key, click 'Add SSH key'" -ForegroundColor White
    Write-Host ""
    Write-Host "  When done, press ENTER here to test the connection." -ForegroundColor Cyan
    Write-Host "  (Ctrl+C to abort if you need to come back later)" -ForegroundColor DarkGray
    Read-Host

    # Re-test after user added key
    Write-Host "  Testing GitHub connection..." -ForegroundColor Yellow
    $sshResult2 = ssh -T git@github.com 2>&1 | Out-String

    if ($sshResult2 -match "successfully authenticated") {
        Write-Host "  PASS: $($sshResult2.Trim())" -ForegroundColor Green
    } else {
        Write-Host "  FAIL: GitHub still doesn't recognize the key." -ForegroundColor Red
        Write-Host "  Response: $($sshResult2.Trim())" -ForegroundColor DarkGray
        Write-Host ""
        Write-Host "  Double-check:" -ForegroundColor Yellow
        Write-Host "    - Did you paste the FULL key (starts with ssh-ed25519)?" -ForegroundColor White
        Write-Host "    - Did you save it on GitHub?" -ForegroundColor White
        Write-Host "    - Try running: ssh -T git@github.com" -ForegroundColor White
        Write-Host ""
        Write-Host "  Fix the issue and re-run this script." -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "  All pre-checks passed." -ForegroundColor Green
Write-Host ""
Write-Host "  Press ENTER to start migration, or Ctrl+C to abort." -ForegroundColor Cyan
Read-Host

# ==========================================================================
# STEP 1/6: Remove backtester's standalone .git folder
# ==========================================================================
# The backtester (PROJECTS\four-pillars-backtester) has its own git repo
# pointing to S23Web3/ni9htw4lker. We remove it so the vault becomes ONE
# flat repo. The backtester source code stays -- only the .git metadata goes.
#
# Same for bingx-connector if it has its own .git.
# ==========================================================================

Write-Host "[Step 1/6] Removing sub-project .git folders..." -ForegroundColor Yellow
Write-Host "  WHY: We want one flat repo for the entire vault." -ForegroundColor DarkGray
Write-Host "       Sub-project .git folders would create nested repos (bad)." -ForegroundColor DarkGray
Write-Host "       Your source code is NOT deleted -- only .git metadata." -ForegroundColor DarkGray
Write-Host ""

$backtesterGit = Join-Path $VAULT "PROJECTS\four-pillars-backtester\.git"
if (Test-Path $backtesterGit) {
    try {
        Remove-Item -Recurse -Force $backtesterGit
        Write-Host "  REMOVED: $backtesterGit" -ForegroundColor Green
    } catch {
        Write-Host "  FAIL: Could not remove $backtesterGit" -ForegroundColor Red
        Write-Host "  Likely a program has files locked (VSCode, Obsidian)." -ForegroundColor Yellow
        Write-Host "  Close those programs and re-run, or delete manually:" -ForegroundColor Yellow
        Write-Host "    Remove-Item -Recurse -Force `"$backtesterGit`"" -ForegroundColor White
        exit 1
    }
} else {
    Write-Host "  SKIP: backtester .git not found (already removed)" -ForegroundColor DarkGray
}

$bingxGit = Join-Path $VAULT "PROJECTS\bingx-connector\.git"
if (Test-Path $bingxGit) {
    try {
        Remove-Item -Recurse -Force $bingxGit
        Write-Host "  REMOVED: $bingxGit" -ForegroundColor Green
    } catch {
        Write-Host "  FAIL: Could not remove $bingxGit" -ForegroundColor Red
        Write-Host "  Close programs that may have files locked and re-run." -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "  SKIP: bingx-connector .git not found (already removed)" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "  Step 1 complete." -ForegroundColor Green
Write-Host "  Press ENTER to continue..." -ForegroundColor Cyan
Read-Host

# ==========================================================================
# STEP 2/6: Initialize git repo at vault root
# ==========================================================================
# git init creates .git/ in the vault root. This is where all version
# history will live. Safe operation -- doesn't touch your files.
# ==========================================================================

Write-Host "[Step 2/6] Initializing git repo at vault root..." -ForegroundColor Yellow
Write-Host "  WHY: This makes the vault a git repository." -ForegroundColor DarkGray
Write-Host "       All version history lives in .git/ folder." -ForegroundColor DarkGray
Write-Host "       Your files are NOT modified." -ForegroundColor DarkGray
Write-Host ""

Set-Location $VAULT

$existingGit = Join-Path $VAULT ".git"
if (Test-Path $existingGit) {
    Write-Host "  SKIP: Git repo already exists at $VAULT" -ForegroundColor DarkGray
} else {
    git init
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  FAIL: git init failed." -ForegroundColor Red
        exit 1
    }
    Write-Host "  DONE: Git repo initialized at $VAULT" -ForegroundColor Green
}

Write-Host ""
Write-Host "  Step 2 complete." -ForegroundColor Green
Write-Host "  Press ENTER to continue..." -ForegroundColor Cyan
Read-Host

# ==========================================================================
# STEP 3/6: Create .gitignore and .gitattributes
# ==========================================================================
# .gitignore tells git which files to NEVER track.
# Critical for keeping secrets and 33GB of data out of the repo.
#
# .gitattributes handles line ending conversion between Windows and Linux.
# Windows uses CRLF (\r\n), Linux uses LF (\n). Bash scripts MUST be LF.
#
# Categories excluded by .gitignore:
#   - Heavy data dirs (cache, csv, periods, historical, coingecko) = 33GB
#   - Python build artifacts (__pycache__, .pyc, dist, build)
#   - Secrets (.env files, Tv.md with TradingView creds)
#   - Obsidian local-only state (workspace.json)
#   - Claude Code temp files (tmpclaude-*)
#   - OS junk (Thumbs.db, desktop.ini)
#   - Large model files (.pkl, .joblib, .h5, .onnx)
#   - Bot runtime logs (regenerated on each run)
#   - Local postgres data
# ==========================================================================

Write-Host "[Step 3/6] Creating .gitignore and .gitattributes..." -ForegroundColor Yellow
Write-Host "  WHY: .gitignore keeps 33GB of data and secrets out of the repo." -ForegroundColor DarkGray
Write-Host "       .gitattributes converts line endings for Linux compatibility." -ForegroundColor DarkGray
Write-Host ""

$gitignorePath = Join-Path $VAULT ".gitignore"

if (Test-Path $gitignorePath) {
    Write-Host "  SKIP: .gitignore already exists (using existing file)" -ForegroundColor DarkGray
} else {

$gitignoreContent = @"
# ==========================================================================
# .gitignore -- Obsidian Vault (S23Web3/Vault)
# ==========================================================================
# Created: 2026-02-26 by migrate_pc.ps1
# Purpose: Exclude heavy data, secrets, and build artifacts from git.
#          The vault repo should be <500MB. Data (33GB) stays local only.
# ==========================================================================

# --- Heavy data (33GB total) -- backtester only, stays on PC ---
PROJECTS/four-pillars-backtester/data/cache/
PROJECTS/four-pillars-backtester/data/csv/
PROJECTS/four-pillars-backtester/data/periods/
PROJECTS/four-pillars-backtester/data/historical/
PROJECTS/four-pillars-backtester/data/coingecko/

# --- Python build artifacts ---
__pycache__/
*.pyc
*.pyo
*.egg-info/
*.eggs/
dist/
build/
*.egg

# --- Secrets (NEVER commit) ---
.env
*.env
Tv.md

# --- Obsidian local-only state ---
.obsidian/workspace.json
.obsidian/workspace-mobile.json

# --- Claude Code temp files ---
tmpclaude-*

# --- OS artifacts ---
.DS_Store
Thumbs.db
desktop.ini

# --- Large model/binary files ---
*.pkl
*.joblib
*.h5
*.onnx

# --- Bot runtime logs (regenerated each run) ---
PROJECTS/bingx-connector/logs/*.log
PROJECTS/bingx-connector/bot.log
PROJECTS/four-pillars-backtester/logs/

# --- Local postgres data directory ---
postgres/

# --- Windows null device artifact ---
nul

# --- pytest cache ---
.pytest_cache/
"@

# Write WITHOUT BOM. PowerShell 5.1's -Encoding UTF8 adds a BOM byte
# which can confuse some git versions. We use .NET directly for clean UTF-8.
[System.IO.File]::WriteAllText($gitignorePath, $gitignoreContent, (New-Object System.Text.UTF8Encoding $false))
Write-Host "  CREATED: $gitignorePath" -ForegroundColor Green
}

# .gitattributes
$gitattributesPath = Join-Path $VAULT ".gitattributes"

if (Test-Path $gitattributesPath) {
    Write-Host "  SKIP: .gitattributes already exists" -ForegroundColor DarkGray
} else {
$gitattributesContent = @"
# Auto-detect text files and normalize line endings
* text=auto

# Force LF for scripts (bash chokes on CRLF)
*.sh text eol=lf
*.py text eol=lf
*.yaml text eol=lf
*.yml text eol=lf

# Force CRLF for Windows-only scripts
*.ps1 text eol=crlf

# Binary files -- don't touch
*.png binary
*.jpg binary
*.pdf binary
*.pkl binary
*.parquet binary
"@

[System.IO.File]::WriteAllText($gitattributesPath, $gitattributesContent, (New-Object System.Text.UTF8Encoding $false))
Write-Host "  CREATED: $gitattributesPath" -ForegroundColor Green
}

Write-Host ""
Write-Host "  Step 3 complete." -ForegroundColor Green
Write-Host "  Press ENTER to continue..." -ForegroundColor Cyan
Read-Host

# ==========================================================================
# STEP 4/6: Stage all files and show summary
# ==========================================================================
# git add . stages everything not excluded by .gitignore.
# We then show a summary so you can review before committing.
# Safety check: blocks commit if any secrets/data files sneak through.
# ==========================================================================

Write-Host "[Step 4/6] Staging files..." -ForegroundColor Yellow
Write-Host "  WHY: git add . tells git to track all files not in .gitignore." -ForegroundColor DarkGray
Write-Host "       We then check nothing dangerous got through." -ForegroundColor DarkGray
Write-Host ""

git add .

# Count what's staged
$stagedFiles = git diff --cached --name-only
$fileCount = ($stagedFiles | Measure-Object).Count

Write-Host "  Staged: $fileCount files" -ForegroundColor Green
Write-Host ""

# Safety check: look for things that should NOT be staged
$dangerous = $stagedFiles | Where-Object {
    $_ -match "\.env$" -or
    $_ -match "\.csv$" -or
    $_ -match "\.parquet$" -or
    $_ -match "__pycache__" -or
    $_ -match "Tv\.md$"
}

if ($dangerous) {
    Write-Host "  DANGER: These files should NOT be committed:" -ForegroundColor Red
    $dangerous | ForEach-Object { Write-Host "    $_" -ForegroundColor Red }
    Write-Host ""
    Write-Host "  Unstaging everything. Fix .gitignore and re-run." -ForegroundColor Red
    git reset HEAD -- . > $null 2>&1
    exit 1
}

Write-Host "  Safety check PASSED: no secrets, no data files, no __pycache__." -ForegroundColor Green
Write-Host ""

# Show file type breakdown
Write-Host "  File type breakdown:" -ForegroundColor Cyan
$stagedFiles | ForEach-Object { [System.IO.Path]::GetExtension($_) } |
    Group-Object | Sort-Object Count -Descending | Select-Object -First 10 |
    ForEach-Object { Write-Host ("    {0,6} {1}" -f $_.Count, $_.Name) }

Write-Host ""
Write-Host "  Step 4 complete." -ForegroundColor Green
Write-Host "  Press ENTER to continue to commit..." -ForegroundColor Cyan
Read-Host

# ==========================================================================
# STEP 5/6: Commit
# ==========================================================================
# Creates the actual git commit with all staged files.
# Re-run safety: if a previous run already committed, fileCount will be 0
# and we skip straight to push.
# ==========================================================================

if ($fileCount -eq 0) {
    Write-Host "[Step 5/6] Nothing new to stage -- previous commit exists." -ForegroundColor DarkGray
    Write-Host "  Skipping to push..." -ForegroundColor DarkGray
} else {
    Write-Host "[Step 5/6] Committing $fileCount files..." -ForegroundColor Yellow
    Write-Host "  WHY: This saves a snapshot of all staged files in git history." -ForegroundColor DarkGray
    Write-Host ""

    git commit -m "Initial vault commit -- source code, docs, strategy, logs (no data/secrets)"

    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "  FAIL: git commit failed." -ForegroundColor Red
        Write-Host "  Check the error message above." -ForegroundColor Yellow
        Write-Host "  Common cause: git user identity not set (should have been caught in pre-check)." -ForegroundColor Yellow
        exit 1
    }

    Write-Host ""
    Write-Host "  DONE: Commit created." -ForegroundColor Green
}

Write-Host ""
Write-Host "  Step 5 complete." -ForegroundColor Green
Write-Host "  Press ENTER to push to GitHub..." -ForegroundColor Cyan
Read-Host

# ==========================================================================
# STEP 6/6: Add remote and push
# ==========================================================================
# The repo S23Web3/Vault was already created on GitHub (private).
# We add it as the 'origin' remote and push the main branch.
# After this, your vault is backed up on GitHub.
# ==========================================================================

Write-Host "[Step 6/6] Pushing to GitHub..." -ForegroundColor Yellow
Write-Host "  WHY: This uploads your commit to https://github.com/S23Web3/Vault" -ForegroundColor DarkGray
Write-Host ""

# Check if remote already exists
$remotes = git remote
if ($remotes -contains "origin") {
    Write-Host "  Remote 'origin' already exists, updating URL..." -ForegroundColor DarkGray
    git remote set-url origin "git@github.com:S23Web3/Vault.git"
} else {
    git remote add origin "git@github.com:S23Web3/Vault.git"
    Write-Host "  Added remote: git@github.com:S23Web3/Vault.git" -ForegroundColor Green
}

git branch -M main
git push -u origin main

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "  FAIL: git push failed." -ForegroundColor Red
    Write-Host "  Your commit is safe locally. Nothing was lost." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Common causes:" -ForegroundColor Yellow
    Write-Host "    - SSH key not added to GitHub (re-run script to re-check)" -ForegroundColor White
    Write-Host "    - Repo S23Web3/Vault doesn't exist on GitHub" -ForegroundColor White
    Write-Host "    - Network issue (try again later)" -ForegroundColor White
    Write-Host ""
    Write-Host "  To retry push manually:" -ForegroundColor Yellow
    Write-Host "    cd `"$VAULT`"" -ForegroundColor White
    Write-Host "    git push -u origin main" -ForegroundColor White
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " MIGRATION COMPLETE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Repo:  https://github.com/S23Web3/Vault" -ForegroundColor Cyan
Write-Host "  Files: $fileCount committed" -ForegroundColor Cyan
Write-Host ""
Write-Host "  NEXT STEPS:" -ForegroundColor Yellow
Write-Host "    1. Check the repo: https://github.com/S23Web3/Vault" -ForegroundColor White
Write-Host "    2. Upload setup_vps.sh to VPS:" -ForegroundColor White
Write-Host '       scp "C:\Users\User\Documents\Obsidian Vault\scripts\setup_vps.sh" root@76.13.20.191:/root/' -ForegroundColor White
Write-Host "    3. SSH in and run it:" -ForegroundColor White
Write-Host "       ssh root@76.13.20.191" -ForegroundColor White
Write-Host "       chmod +x /root/setup_vps.sh" -ForegroundColor White
Write-Host "       ./setup_vps.sh" -ForegroundColor White
Write-Host ""
