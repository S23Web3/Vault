# Install Python 3.12 + Numba CUDA for Four Pillars GPU Sweep

**Why**: Numba 0.61 CUDA kernels crash on Python 3.13 (access violation in `cuCtxGetDevice`).
Python 3.12 is the newest version with full Numba CUDA support.

**What this does**: Installs Python 3.12 side-by-side (does NOT replace 3.13), creates a venv,
installs all backtester dependencies + numba CUDA toolkit, and verifies GPU access.

---

## PowerShell Script

Save as `install_py312_cuda.ps1` and run from an **elevated** (admin) PowerShell if the
Python installer needs admin, or run non-elevated if you choose "Install for current user only".

```powershell
# install_py312_cuda.ps1
# Installs Python 3.12 + Numba CUDA venv for Four Pillars backtester.
# Run from: C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester

$ErrorActionPreference = "Stop"

$PY312_URL    = "https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe"
$INSTALLER    = "$env:TEMP\python-3.12.8-amd64.exe"
$INSTALL_DIR  = "C:\Python312"
$VENV_DIR     = "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\.venv312"
$PROJECT_ROOT = "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester"

Write-Host "=== Step 1: Download Python 3.12.8 ===" -ForegroundColor Cyan
if (Test-Path "$INSTALL_DIR\python.exe") {
    Write-Host "Python 3.12 already installed at $INSTALL_DIR" -ForegroundColor Yellow
} else {
    if (-not (Test-Path $INSTALLER)) {
        Write-Host "Downloading from python.org..."
        Invoke-WebRequest -Uri $PY312_URL -OutFile $INSTALLER -UseBasicParsing
    }
    Write-Host "Installing Python 3.12 to $INSTALL_DIR (silent, no PATH modification)..."
    Start-Process -Wait -FilePath $INSTALLER -ArgumentList @(
        "/quiet",
        "InstallAllUsers=0",
        "TargetDir=$INSTALL_DIR",
        "PrependPath=0",
        "Include_launcher=0",
        "Include_test=0"
    )
    if (-not (Test-Path "$INSTALL_DIR\python.exe")) {
        Write-Host "ERROR: Python 3.12 install failed." -ForegroundColor Red
        exit 1
    }
    Write-Host "Python 3.12 installed." -ForegroundColor Green
}

& "$INSTALL_DIR\python.exe" --version

Write-Host "`n=== Step 2: Create venv ===" -ForegroundColor Cyan
if (Test-Path $VENV_DIR) {
    Write-Host "Venv already exists at $VENV_DIR" -ForegroundColor Yellow
} else {
    & "$INSTALL_DIR\python.exe" -m venv $VENV_DIR
    Write-Host "Venv created." -ForegroundColor Green
}

$PIP = "$VENV_DIR\Scripts\pip.exe"
$PYTHON = "$VENV_DIR\Scripts\python.exe"

Write-Host "`n=== Step 3: Upgrade pip ===" -ForegroundColor Cyan
& $PYTHON -m pip install --upgrade pip

Write-Host "`n=== Step 4: Install core dependencies ===" -ForegroundColor Cyan
# Numba + CUDA toolkit (numba-cuda handles CUDA runtime)
& $PIP install numba numpy pandas streamlit plotly pyarrow

Write-Host "`n=== Step 5: Install backtester dependencies ===" -ForegroundColor Cyan
# All packages the dashboard and engine import
& $PIP install scikit-learn scipy xgboost openpyxl requests pyyaml
& $PIP install reportlab  # PDF export
& $PIP install sqlalchemy psycopg2-binary  # PostgreSQL

Write-Host "`n=== Step 6: Install PyTorch with CUDA 13.0 ===" -ForegroundColor Cyan
& $PIP install torch torchvision --index-url https://download.pytorch.org/whl/cu130

Write-Host "`n=== Step 7: Verify Numba CUDA ===" -ForegroundColor Cyan
& $PYTHON -c @"
import numba
from numba import cuda
print('Numba version:', numba.__version__)
print('CUDA available:', cuda.is_available())
if cuda.is_available():
    dev = cuda.get_current_device()
    name = dev.name
    if isinstance(name, bytes):
        name = name.decode()
    print('Device:', name)
    free, total = cuda.current_context().get_memory_info()
    print('VRAM: {:.1f} GB free / {:.1f} GB total'.format(free/1024**3, total/1024**3))
else:
    print('WARNING: CUDA not available. Check NVIDIA driver.')
    cuda.detect()
"@

Write-Host "`n=== Step 8: Verify backtester imports ===" -ForegroundColor Cyan
Push-Location $PROJECT_ROOT
& $PYTHON -c @"
import sys
sys.path.insert(0, '.')
from engine.cuda_sweep import get_cuda_info
info = get_cuda_info()
if info:
    print('GPU sweep ready:', info['device'])
else:
    print('WARNING: get_cuda_info() returned None')
from engine.jit_backtest import ensure_warmup
ensure_warmup()
print('JIT warmup complete')
"@
Pop-Location

Write-Host "`n=== DONE ===" -ForegroundColor Green
Write-Host "Activate venv:  $VENV_DIR\Scripts\Activate.ps1"
Write-Host "Run dashboard:  & `"$PYTHON`" -m streamlit run `"$PROJECT_ROOT\scripts\dashboard_v394.py`""
Write-Host "Or after activating venv:  streamlit run scripts/dashboard_v394.py"
```

---

## Quick Reference

```powershell
# Activate the venv
& "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\.venv312\Scripts\Activate.ps1"

# Run build script (creates cuda_sweep.py, jit_backtest.py, dashboard_v394.py)
python scripts/build_cuda_engine.py

# Verify CUDA
python -c "from engine.cuda_sweep import get_cuda_info; print(get_cuda_info())"

# Launch dashboard
streamlit run scripts/dashboard_v394.py

# Deactivate when done
deactivate
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `cuda.is_available() = False` | Update NVIDIA driver to 527+. Run `nvidia-smi` to check. |
| `ModuleNotFoundError: numba` | Activate the venv first: `.venv312\Scripts\Activate.ps1` |
| Installer needs admin | Run PowerShell as Administrator, or change `InstallAllUsers=0` |
| `CUDA_ERROR_NOT_INITIALIZED` | Restart terminal after driver update. Close any GPU-heavy apps. |
| Wrong Python runs | Use full path: `.venv312\Scripts\python.exe` instead of `python` |
