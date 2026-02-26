<#
.SYNOPSIS
    Four Pillars Backtester - Full Environment Setup Script
.DESCRIPTION
    Automated installer for the Four Pillars trading backtester.
    Installs: NVIDIA Driver, CUDA 13.1, Git, Python 3.13, VS Code,
    all Python packages (PyTorch+CUDA, XGBoost, Optuna, etc.)

    Idempotent: detects what's already installed and skips it.
    Safe to re-run on a machine that's already set up.

.USAGE
    Run as Administrator in PowerShell:
    Set-ExecutionPolicy Bypass -Scope Process -Force
    .\setup.ps1

    To skip downloads and use local installers:
    .\setup.ps1 -LocalInstallers "C:\Installers"

.NOTES
    Last updated: 2026-02-09
    Tested on: Windows 11, RTX 3060 12GB
#>

param(
    [string]$LocalInstallers = "$env:USERPROFILE\Downloads",
    [string]$ProjectPath = "$env:USERPROFILE\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester",
    [switch]$SkipFetch,
    [switch]$DryRun
)

# ============================================================================
# Admin Check (soft - warns but allows DryRun without elevation)
# ============================================================================

$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator
)

if (-not $isAdmin -and -not $DryRun) {
    Write-Host "WARNING: Not running as Administrator." -ForegroundColor Red
    Write-Host "Some installs (NVIDIA, CUDA, VS Community) require elevation." -ForegroundColor Red
    Write-Host "Re-run with: Start-Process powershell -Verb RunAs -ArgumentList '-File setup.ps1'" -ForegroundColor Yellow
    Write-Host ""
    $continue = Read-Host "Continue anyway for pip-only installs? (y/n)"
    if ($continue -ne "y") { exit 1 }
}

# ============================================================================
# Configuration - Download URLs (fallback if local installers not found)
# ============================================================================

$CONFIG = @{
    # NVIDIA Driver (RTX 3060)
    NvidiaDriver = @{
        LocalFile = "591.74-desktop-win10-win11-64bit-international-nsd-dch-whql.exe"
        Url       = "https://us.download.nvidia.com/Windows/591.74/591.74-desktop-win10-win11-64bit-international-nsd-dch-whql.exe"
        Silent    = "/s /noreboot"
    }
    # CUDA Toolkit 13.1
    Cuda = @{
        LocalFile = "cuda_13.1.1_windows.exe"
        Url       = "https://developer.download.nvidia.com/compute/cuda/13.1.1/local_installers/cuda_13.1.1_windows.exe"
        Silent    = "-s"
    }
    # Git
    Git = @{
        LocalFile = "Git-2.52.0-64-bit.exe"
        Url       = "https://github.com/git-for-windows/git/releases/download/v2.52.0.windows.1/Git-2.52.0-64-bit.exe"
        Silent    = "/VERYSILENT /NORESTART"
    }
    # Visual Studio Community 2022 (C++ build tools for CUDA)
    VSCommunity = @{
        LocalFile = "vs_Community.exe"
        Url       = "https://aka.ms/vs/17/release/vs_community.exe"
        Silent    = "--add Microsoft.VisualStudio.Workload.NativeDesktop --includeRecommended --passive --norestart --wait"
    }
    # VS Code
    VSCode = @{
        LocalFile = "VSCodeUserSetup-x64-1.108.1.exe"
        Url       = "https://update.code.visualstudio.com/latest/win32-x64-user/stable"
        Silent    = "/VERYSILENT /NORESTART /MERGETASKS=!runcode,addcontextmenufiles,addcontextmenufolders,addtopath"
    }
    # PyTorch CUDA index
    TorchIndex = "https://download.pytorch.org/whl/cu130"
}

# ============================================================================
# Helper Functions
# ============================================================================

$script:stepNum = 0
$script:passCount = 0
$script:skipCount = 0
$script:failCount = 0

function Write-Step {
    param([string]$Message)
    $script:stepNum++
    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host "  STEP $($script:stepNum): $Message" -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor Cyan
}

function Write-Status {
    param([string]$Message, [string]$Status = "INFO")
    $color = switch ($Status) {
        "OK"      { "Green" }
        "SKIP"    { "Yellow" }
        "FAIL"    { "Red" }
        "WARN"    { "DarkYellow" }
        "RUN"     { "White" }
        default   { "Gray" }
    }
    $prefix = switch ($Status) {
        "OK"      { "[OK]    " }
        "SKIP"    { "[SKIP]  " }
        "FAIL"    { "[FAIL]  " }
        "WARN"    { "[WARN]  " }
        "RUN"     { "[RUN]   " }
        default   { "[INFO]  " }
    }
    Write-Host "$prefix$Message" -ForegroundColor $color
}

function Get-InstallerPath {
    param([hashtable]$Component)
    $localPath = Join-Path $LocalInstallers $Component.LocalFile
    if (Test-Path $localPath) {
        return $localPath
    }
    return $null
}

function Save-Installer {
    param([hashtable]$Component, [string]$DownloadDir)
    $dest = Join-Path $DownloadDir $Component.LocalFile
    if (Test-Path $dest) {
        Write-Status "Already downloaded: $($Component.LocalFile)" "SKIP"
        return $dest
    }
    Write-Status "Downloading $($Component.LocalFile)..." "RUN"
    try {
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $Component.Url -OutFile $dest -UseBasicParsing
        Write-Status "Downloaded to $dest" "OK"
        return $dest
    }
    catch {
        Write-Status "Download failed: $_" "FAIL"
        return $null
    }
}

# ============================================================================
# Pre-flight checks
# ============================================================================

Write-Host ""
Write-Host "================================================================" -ForegroundColor White
Write-Host "  FOUR PILLARS BACKTESTER - ENVIRONMENT SETUP" -ForegroundColor White
Write-Host "  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host "================================================================" -ForegroundColor White
Write-Host ""
Write-Host "  Local installers: $LocalInstallers"
Write-Host "  Project path:     $ProjectPath"
Write-Host "  Dry run:          $DryRun"
Write-Host ""

if ($DryRun) {
    Write-Status "DRY RUN MODE - no changes will be made" "WARN"
}

# ============================================================================
# STEP 1: NVIDIA Driver
# ============================================================================

Write-Step "NVIDIA GPU Driver"

$gpu = $null
try {
    $gpu = nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader 2>$null
}
catch {}

if ($gpu) {
    Write-Status "GPU detected: $gpu" "OK"
    $script:skipCount++
}
else {
    Write-Status "NVIDIA driver not found" "WARN"
    $installer = Get-InstallerPath $CONFIG.NvidiaDriver
    if (-not $installer) {
        Write-Status "Installer not found locally. Download from:" "INFO"
        Write-Status "  $($CONFIG.NvidiaDriver.Url)" "INFO"
        $installer = Save-Installer $CONFIG.NvidiaDriver $LocalInstallers
    }
    if ($installer -and -not $DryRun) {
        Write-Status "Installing NVIDIA driver (this may take a few minutes)..." "RUN"
        Start-Process -FilePath $installer -ArgumentList $CONFIG.NvidiaDriver.Silent -Wait
        Write-Status "NVIDIA driver installed. REBOOT REQUIRED." "WARN"
    }
}

# ============================================================================
# STEP 2: Visual Studio Community 2022 (C++ Build Tools)
# ============================================================================

Write-Step "Visual Studio Community 2022 (C++ Build Tools)"

$vsInstalled = Test-Path "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC"
$vsBTInstalled = Test-Path "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC"

if ($vsInstalled -or $vsBTInstalled) {
    $vsPath = if ($vsInstalled) { "Community" } else { "BuildTools" }
    Write-Status "Visual Studio 2022 $vsPath - C++ tools found" "OK"
    $script:skipCount++
}
else {
    Write-Status "Visual Studio C++ build tools not found" "WARN"
    Write-Status "Required for: CUDA toolkit, C extension compilation" "INFO"
    $installer = Get-InstallerPath $CONFIG.VSCommunity
    if (-not $installer) {
        Write-Status "Installer not found locally. Download from:" "INFO"
        Write-Status "  $($CONFIG.VSCommunity.Url)" "INFO"
        $installer = Save-Installer $CONFIG.VSCommunity $LocalInstallers
    }
    if ($installer -and -not $DryRun) {
        Write-Status "Installing VS Community 2022 with C++ Desktop workload..." "RUN"
        Write-Status "This takes 10-20 minutes (several GB download)..." "INFO"
        Start-Process -FilePath $installer -ArgumentList $CONFIG.VSCommunity.Silent -Wait
        Write-Status "Visual Studio Community 2022 installed" "OK"
        $script:passCount++
    }
}

# ============================================================================
# STEP 3: CUDA Toolkit
# ============================================================================

Write-Step "NVIDIA CUDA Toolkit 13.1"

$cudaInstalled = Test-Path "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.1\bin\nvcc.exe"

if ($cudaInstalled) {
    $nvccVer = & "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.1\bin\nvcc.exe" --version 2>$null | Select-String "release"
    Write-Status "CUDA 13.1 installed: $nvccVer" "OK"
    $script:skipCount++
}
else {
    Write-Status "CUDA 13.1 not found" "WARN"
    $installer = Get-InstallerPath $CONFIG.Cuda
    if (-not $installer) {
        Write-Status "Installer not found locally. Download from:" "INFO"
        Write-Status "  $($CONFIG.Cuda.Url)" "INFO"
        $installer = Save-Installer $CONFIG.Cuda $LocalInstallers
    }
    if ($installer -and -not $DryRun) {
        Write-Status "Installing CUDA 13.1 (this takes several minutes)..." "RUN"
        Start-Process -FilePath $installer -ArgumentList $CONFIG.Cuda.Silent -Wait
        # Add to PATH for current session
        $env:Path += ";C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.1\bin"
        Write-Status "CUDA 13.1 installed" "OK"
        $script:passCount++
    }
}

# ============================================================================
# STEP 3: Git
# ============================================================================

Write-Step "Git"

$gitVer = $null
try { $gitVer = git --version 2>$null } catch {}

if ($gitVer) {
    Write-Status "Git installed: $gitVer" "OK"
    $script:skipCount++
}
else {
    $installer = Get-InstallerPath $CONFIG.Git
    if (-not $installer) {
        $installer = Save-Installer $CONFIG.Git $LocalInstallers
    }
    if ($installer -and -not $DryRun) {
        Write-Status "Installing Git..." "RUN"
        Start-Process -FilePath $installer -ArgumentList $CONFIG.Git.Silent -Wait
        $env:Path += ";C:\Program Files\Git\bin"
        Write-Status "Git installed" "OK"
        $script:passCount++
    }
}

# ============================================================================
# STEP 4: Python 3.13 (Microsoft Store)
# ============================================================================

Write-Step "Python 3.13"

$pyVer = $null
try { $pyVer = python --version 2>$null } catch {}

if ($pyVer -and $pyVer -match "3\.13") {
    Write-Status "Python installed: $pyVer" "OK"
    $script:skipCount++
}
elseif ($pyVer) {
    Write-Status "Python found but wrong version: $pyVer (need 3.13)" "WARN"
    Write-Status "Install Python 3.13 from Microsoft Store manually" "INFO"
    $script:failCount++
}
else {
    Write-Status "Python not found" "WARN"
    Write-Status "Install Python 3.13 from Microsoft Store:" "INFO"
    Write-Status "  1. Open Microsoft Store" "INFO"
    Write-Status "  2. Search 'Python 3.13'" "INFO"
    Write-Status "  3. Click Install" "INFO"
    Write-Status "" "INFO"
    Write-Status "Or use winget:" "INFO"
    if (-not $DryRun) {
        Write-Status "Attempting winget install..." "RUN"
        try {
            winget install Python.Python.3.13 --accept-package-agreements --accept-source-agreements 2>$null
            Write-Status "Python 3.13 installed via winget" "OK"
            $script:passCount++
        }
        catch {
            Write-Status "winget failed - install Python 3.13 from Microsoft Store manually" "FAIL"
            $script:failCount++
        }
    }
}

# ============================================================================
# STEP 5: VS Code
# ============================================================================

Write-Step "Visual Studio Code"

$codeVer = $null
try { $codeVer = code --version 2>$null | Select-Object -First 1 } catch {}

if ($codeVer) {
    Write-Status "VS Code installed: v$codeVer" "OK"
    $script:skipCount++
}
else {
    $installer = Get-InstallerPath $CONFIG.VSCode
    if (-not $installer) {
        $installer = Save-Installer $CONFIG.VSCode $LocalInstallers
    }
    if ($installer -and -not $DryRun) {
        Write-Status "Installing VS Code..." "RUN"
        Start-Process -FilePath $installer -ArgumentList $CONFIG.VSCode.Silent -Wait
        Write-Status "VS Code installed" "OK"
        $script:passCount++
    }
}

# ============================================================================
# STEP 6: Python Packages - Core
# ============================================================================

Write-Step "Python Packages - Core (pandas, numpy, pyarrow, etc.)"

# Check if Python is available
$pyAvailable = $false
try {
    $pyCheck = python --version 2>$null
    if ($pyCheck -match "3\.13") { $pyAvailable = $true }
}
catch {}

if (-not $pyAvailable) {
    Write-Status "Python 3.13 not available - skipping package install" "FAIL"
    Write-Status "Install Python 3.13 first, then re-run this script" "INFO"
    $script:failCount++
}
else {
    $corePackages = @(
        "requests",
        "pandas",
        "numpy",
        "pyarrow",
        "pyyaml",
        "python-dotenv",
        "streamlit",
        "plotly",
        "matplotlib",
        "scikit-learn"
    )

    foreach ($pkg in $corePackages) {
        $installed = python -m pip show $pkg 2>$null
        if ($installed) {
            $ver = ($installed | Select-String "Version:").ToString().Split(":")[1].Trim()
            Write-Status "$pkg==$ver" "SKIP"
            $script:skipCount++
        }
        else {
            if (-not $DryRun) {
                Write-Status "Installing $pkg..." "RUN"
                python -m pip install $pkg --quiet 2>$null
                $script:passCount++
            }
            else {
                Write-Status "Would install: $pkg" "INFO"
            }
        }
    }
}

# ============================================================================
# STEP 7: Python Packages - ML (PyTorch, XGBoost, Optuna)
# ============================================================================

Write-Step "Python Packages - ML (PyTorch+CUDA, XGBoost, Optuna)"

if ($pyAvailable) {
    # PyTorch
    $torchInstalled = python -c "import torch; print(torch.__version__)" 2>$null
    if ($torchInstalled -and $torchInstalled -match "cu130") {
        Write-Status "PyTorch $torchInstalled (CUDA)" "SKIP"
        $script:skipCount++
    }
    else {
        if (-not $DryRun) {
            Write-Status "Installing PyTorch + CUDA 13.0 (~1.9 GB download)..." "RUN"
            python -m pip install torch torchvision --index-url $CONFIG.TorchIndex --quiet 2>$null
            $torchCheck = python -c "import torch; print(f'{torch.__version__} CUDA={torch.cuda.is_available()}')" 2>$null
            Write-Status "PyTorch $torchCheck" "OK"
            $script:passCount++
        }
        else {
            Write-Status "Would install: torch torchvision (cu130)" "INFO"
        }
    }

    # XGBoost
    $xgbInstalled = python -c "import xgboost; print(xgboost.__version__)" 2>$null
    if ($xgbInstalled) {
        Write-Status "XGBoost $xgbInstalled" "SKIP"
        $script:skipCount++
    }
    else {
        if (-not $DryRun) {
            Write-Status "Installing XGBoost..." "RUN"
            python -m pip install xgboost --quiet 2>$null
            $script:passCount++
        }
    }

    # Optuna
    $optunaInstalled = python -c "import optuna; print(optuna.__version__)" 2>$null
    if ($optunaInstalled) {
        Write-Status "Optuna $optunaInstalled" "SKIP"
        $script:skipCount++
    }
    else {
        if (-not $DryRun) {
            Write-Status "Installing Optuna..." "RUN"
            python -m pip install optuna --quiet 2>$null
            $script:passCount++
        }
    }
}

# ============================================================================
# STEP 8: Project Setup
# ============================================================================

Write-Step "Project Directory"

if (Test-Path $ProjectPath) {
    $parquets = Get-ChildItem "$ProjectPath\data\cache\*_1m.parquet" -ErrorAction SilentlyContinue
    Write-Status "Project exists at: $ProjectPath" "OK"
    if ($parquets) {
        $totalMB = ($parquets | Measure-Object -Property Length -Sum).Sum / 1MB
        Write-Status "Cache: $($parquets.Count) coins, $([math]::Round($totalMB)) MB" "OK"
    }
    else {
        Write-Status "No cached data yet - run fetch after setup" "WARN"
    }
    $script:skipCount++
}
else {
    Write-Status "Project directory not found: $ProjectPath" "WARN"
    Write-Status "Clone the repo or copy the project folder from the reference machine" "INFO"
    Write-Status "  git clone https://github.com/S23Web3/ni9htw4lker.git `"$($ProjectPath | Split-Path -Parent | Split-Path -Parent)`"" "INFO"
    $script:failCount++
}

# ============================================================================
# STEP 9: Full Verification
# ============================================================================

Write-Step "Environment Verification"

if ($pyAvailable) {
    $verifyScript = @"
import sys
results = []

def check(name, test):
    try:
        ver = test()
        results.append(('OK', name, ver))
    except Exception as e:
        results.append(('FAIL', name, str(e)))

check('Python', lambda: sys.version.split()[0])
check('NumPy', lambda: __import__('numpy').__version__)
check('Pandas', lambda: __import__('pandas').__version__)
check('PyArrow', lambda: __import__('pyarrow').__version__)
check('Requests', lambda: __import__('requests').__version__)
check('PyYAML', lambda: __import__('yaml').__version__)
check('Streamlit', lambda: __import__('streamlit').__version__)
check('Plotly', lambda: __import__('plotly').__version__)
check('Matplotlib', lambda: __import__('matplotlib').__version__)
check('Scikit-learn', lambda: __import__('sklearn').__version__)

# ML packages
try:
    import torch
    cuda_status = f'{torch.__version__} CUDA={torch.cuda.is_available()}'
    if torch.cuda.is_available():
        cuda_status += f' ({torch.cuda.get_device_name(0)})'
    results.append(('OK', 'PyTorch', cuda_status))
except Exception as e:
    results.append(('FAIL', 'PyTorch', str(e)))

check('XGBoost', lambda: __import__('xgboost').__version__)
check('Optuna', lambda: __import__('optuna').__version__)

for status, name, ver in results:
    print(f'{status}|{name}|{ver}')
"@

    $output = python -c $verifyScript 2>$null
    foreach ($line in $output -split "`n") {
        $parts = $line.Trim() -split "\|"
        if ($parts.Count -ge 3) {
            $status = $parts[0]
            $name = $parts[1]
            $ver = $parts[2]
            if ($status -eq "OK") {
                Write-Status "$($name.PadRight(15)) $ver" "OK"
                $script:passCount++
            }
            else {
                Write-Status "$($name.PadRight(15)) $ver" "FAIL"
                $script:failCount++
            }
        }
    }
}

# ============================================================================
# STEP 10: Data Fetch (optional)
# ============================================================================

Write-Step "Data Fetch"

if (-not (Test-Path $ProjectPath)) {
    Write-Status "Project not found - skipping data fetch" "SKIP"
}
else {
    $parquets = Get-ChildItem "$ProjectPath\data\cache\*_1m.parquet" -ErrorAction SilentlyContinue
    if ($parquets) {
        $totalMB = ($parquets | Measure-Object -Property Length -Sum).Sum / 1MB
        Write-Status "Cache: $($parquets.Count) coins, $([math]::Round($totalMB)) MB" "OK"
    }
    else {
        Write-Status "No cached data found" "WARN"
    }

    Write-Host ""
    Write-Host "  Data options:" -ForegroundColor Cyan
    Write-Host "    1. Skip - I'll copy data from another machine" -ForegroundColor White
    Write-Host "    2. Fetch - Download 3 months of 1m data from Bybit (6-8 hours)" -ForegroundColor White
    Write-Host ""
    $fetchChoice = Read-Host "  Choose (1 or 2)"

    if ($fetchChoice -eq "2" -and -not $DryRun) {
        Write-Status "Starting data fetch (safe to Ctrl+C and resume later)..." "RUN"
        Push-Location $ProjectPath
        python scripts/fetch_sub_1b.py --months 3
        Pop-Location
    }
    else {
        Write-Status "Skipped - copy data\cache\ folder from reference machine" "SKIP"
    }
}

# ============================================================================
# Summary
# ============================================================================

Write-Host ""
Write-Host ("=" * 70) -ForegroundColor White
Write-Host "  SETUP COMPLETE" -ForegroundColor White
Write-Host ("=" * 70) -ForegroundColor White
Write-Host ""
Write-Status "Passed/Installed:  $($script:passCount)" "OK"
Write-Status "Already installed: $($script:skipCount)" "SKIP"
if ($script:failCount -gt 0) {
    Write-Status "Failed/Missing:    $($script:failCount)" "FAIL"
}
else {
    Write-Status "Failed/Missing:    0" "OK"
}
Write-Host ""

if ($script:failCount -gt 0) {
    Write-Status "Some components need attention - check FAIL items above" "WARN"
}
else {
    Write-Status "All components installed and verified!" "OK"
}

Write-Host ""
Write-Host "  Next steps:" -ForegroundColor Gray
Write-Host "    1. Fetch data:  cd `"$ProjectPath`" && python scripts/fetch_sub_1b.py --months 3" -ForegroundColor Gray
Write-Host "    2. Run backtest: python -m engine.backtester" -ForegroundColor Gray
Write-Host "    3. Dashboard:   python -m streamlit run dashboard.py" -ForegroundColor Gray
Write-Host ""
