$ErrorActionPreference = "Stop"

$PY312_URL   = "https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe"
$INSTALLER   = "$env:TEMP\python-3.12.8-amd64.exe"
$INSTALL_DIR = "C:\Python312"
$VENV_DIR    = "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\.venv312"
$PROJECT     = "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester"

# Step 1: Download Python 3.12
Write-Host "=== Download Python 3.12.8 ===" -ForegroundColor Cyan
if (Test-Path "$INSTALL_DIR\python.exe") {
    Write-Host "Already installed at $INSTALL_DIR" -ForegroundColor Yellow
} else {
    if (-not (Test-Path $INSTALLER)) {
        Invoke-WebRequest -Uri $PY312_URL -OutFile $INSTALLER -UseBasicParsing
    }
    Start-Process -Wait -FilePath $INSTALLER -ArgumentList "/quiet", "InstallAllUsers=0", "TargetDir=$INSTALL_DIR", "PrependPath=0", "Include_launcher=0", "Include_test=0"
    if (-not (Test-Path "$INSTALL_DIR\python.exe")) {
        Write-Host "Install failed." -ForegroundColor Red; exit 1
    }
}
& "$INSTALL_DIR\python.exe" --version

# Step 2: Create venv
Write-Host "`n=== Create venv ===" -ForegroundColor Cyan
if (-not (Test-Path $VENV_DIR)) {
    & "$INSTALL_DIR\python.exe" -m venv $VENV_DIR
}

$PIP    = "$VENV_DIR\Scripts\pip.exe"
$PYTHON = "$VENV_DIR\Scripts\python.exe"

# Step 3: Install deps
Write-Host "`n=== Install packages ===" -ForegroundColor Cyan
& $PYTHON -m pip install --upgrade pip
& $PIP install numba numpy pandas streamlit plotly pyarrow scikit-learn scipy xgboost openpyxl requests pyyaml reportlab sqlalchemy psycopg2-binary
& $PIP install torch torchvision --index-url https://download.pytorch.org/whl/cu130

# Step 4: Verify CUDA
Write-Host "`n=== Verify CUDA ===" -ForegroundColor Cyan
Push-Location $PROJECT
& $PYTHON -c "from numba import cuda; print('CUDA available:', cuda.is_available()); cuda.detect()"
& $PYTHON -c "import sys; sys.path.insert(0,'.'); from engine.cuda_sweep import get_cuda_info; print(get_cuda_info())"
Pop-Location

Write-Host "`n=== DONE ===" -ForegroundColor Green
Write-Host "Activate:  & '$VENV_DIR\Scripts\Activate.ps1'"
Write-Host "Dashboard: streamlit run scripts/dashboard_v394.py"
