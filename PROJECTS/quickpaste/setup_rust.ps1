# QuickPaste — Rust Environment Setup Script
# Run from PowerShell as Administrator:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   & "C:\Users\User\Documents\Obsidian Vault\PROJECTS\quickpaste\setup_rust.ps1"

$ErrorActionPreference = "Stop"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Write-Host "[$timestamp] QuickPaste Rust Setup" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# --- Step 1: Check if Rust is already installed ---
Write-Host "`n[1/5] Checking for existing Rust installation..." -ForegroundColor Yellow
$rustcPath = Get-Command rustc -ErrorAction SilentlyContinue
$cargoPath = Get-Command cargo -ErrorAction SilentlyContinue

if ($rustcPath -and $cargoPath) {
    $rustVersion = & rustc --version
    $cargoVersion = & cargo --version
    Write-Host "      Rust already installed: $rustVersion" -ForegroundColor Green
    Write-Host "      Cargo: $cargoVersion" -ForegroundColor Green
    $rustInstalled = $true
} else {
    Write-Host "      Rust not found. Will install via winget." -ForegroundColor Red
    $rustInstalled = $false
}

# --- Step 2: Install Rust via winget ---
if (-not $rustInstalled) {
    Write-Host "`n[2/5] Installing Rust via winget..." -ForegroundColor Yellow

    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $winget) {
        Write-Host "      ERROR: winget not found. Install from Microsoft Store (App Installer)." -ForegroundColor Red
        exit 1
    }

    Write-Host "      Running: winget install Rustlang.Rustup --accept-source-agreements --accept-package-agreements"
    winget install Rustlang.Rustup --accept-source-agreements --accept-package-agreements

    # Reload PATH so rustup/cargo are available in this session
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "User") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "Machine")

    Write-Host "      Rust installed." -ForegroundColor Green
} else {
    Write-Host "`n[2/5] Skipping winget install (Rust already present)." -ForegroundColor Green
}

# --- Step 3: Set up MSVC toolchain ---
Write-Host "`n[3/5] Setting up stable MSVC toolchain..." -ForegroundColor Yellow

$rustupPath = Get-Command rustup -ErrorAction SilentlyContinue
if (-not $rustupPath) {
    # rustup may be in %USERPROFILE%\.cargo\bin after fresh install
    $env:PATH += ";$env:USERPROFILE\.cargo\bin"
    $rustupPath = Get-Command rustup -ErrorAction SilentlyContinue
}

if (-not $rustupPath) {
    Write-Host "      ERROR: rustup not found after install. Restart terminal and re-run." -ForegroundColor Red
    exit 1
}

& rustup toolchain install stable-x86_64-pc-windows-msvc
& rustup default stable-x86_64-pc-windows-msvc
& rustup target add x86_64-pc-windows-msvc
Write-Host "      MSVC toolchain ready." -ForegroundColor Green

# --- Step 4: Install rust-analyzer VSCode extension ---
Write-Host "`n[4/5] Installing rust-analyzer VSCode extension..." -ForegroundColor Yellow

$codePath = Get-Command code -ErrorAction SilentlyContinue
if ($codePath) {
    & code --install-extension rust-lang.rust-analyzer --force
    Write-Host "      rust-analyzer installed." -ForegroundColor Green
} else {
    Write-Host "      WARNING: 'code' command not found. Install rust-analyzer manually:" -ForegroundColor DarkYellow
    Write-Host "      VSCode > Extensions > search 'rust-analyzer' (by rust-lang)" -ForegroundColor DarkYellow
}

# --- Step 5: Verify ---
Write-Host "`n[5/5] Verifying installation..." -ForegroundColor Yellow

$env:PATH += ";$env:USERPROFILE\.cargo\bin"

$checks = @(
    @{ Name = "rustc"; Cmd = "rustc --version" },
    @{ Name = "cargo"; Cmd = "cargo --version" },
    @{ Name = "rustup"; Cmd = "rustup show active-toolchain" }
)

$allOk = $true
foreach ($check in $checks) {
    try {
        $result = Invoke-Expression $check.Cmd 2>&1
        Write-Host "      OK  $($check.Name): $result" -ForegroundColor Green
    } catch {
        Write-Host "      FAIL $($check.Name): not found" -ForegroundColor Red
        $allOk = $false
    }
}

# --- Create project scaffold ---
Write-Host "`n[+] Creating project directory..." -ForegroundColor Yellow
$projectDir = "C:\Users\User\Documents\Obsidian Vault\PROJECTS\quickpaste"
$srcDir = "$projectDir\src"
$assetsDir = "$projectDir\assets"

New-Item -ItemType Directory -Force -Path $srcDir | Out-Null
New-Item -ItemType Directory -Force -Path $assetsDir | Out-Null
Write-Host "      Created: $projectDir" -ForegroundColor Green

# --- Summary ---
Write-Host "`n============================================" -ForegroundColor Cyan
if ($allOk) {
    Write-Host "SETUP COMPLETE — Rust is ready." -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor White
    Write-Host "  1. Open a new terminal (to reload PATH)" -ForegroundColor White
    Write-Host "  2. Run: rustc --version    (should print version)" -ForegroundColor White
    Write-Host "  3. Tell Claude: Rust is installed, build the skill and start Phase 0" -ForegroundColor White
} else {
    Write-Host "SETUP INCOMPLETE — see FAIL lines above." -ForegroundColor Red
    Write-Host "Restart terminal after installing and re-run this script." -ForegroundColor Yellow
}
Write-Host "============================================" -ForegroundColor Cyan
