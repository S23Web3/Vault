"""
Venv setup script for four-pillars-backtester (Python 3.12 + CUDA).

Creates .venv312 at the backtester root, installs all required packages,
and verifies key imports. Requires Python 3.12 at C:/Python312/python.exe.

Run: python scripts/setup_venv312.py
     (can be run with any Python >= 3.8; creates the 3.12 venv via subprocess)
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY312 = Path("C:/Python312/python.exe")
VENV_DIR = ROOT / ".venv312"
PIP = VENV_DIR / "Scripts" / "pip.exe"
PYTHON = VENV_DIR / "Scripts" / "python.exe"


def run(cmd: list, label: str = "") -> bool:
    """Run a subprocess command; print label and return True on success."""
    tag = ("[" + label + "] ") if label else ""
    print(tag + " ".join(str(c) for c in cmd))
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print("  ERROR: exit code " + str(result.returncode))
        return False
    return True


def check_python312() -> bool:
    """Verify Python 3.12 exists at the expected path."""
    if PY312.exists():
        result = subprocess.run([str(PY312), "--version"], capture_output=True, text=True)
        print("Python 3.12 found: " + result.stdout.strip())
        return True
    print("ERROR: Python 3.12 not found at " + str(PY312))
    print("       Install from: https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe")
    print("       Use: Install for current user only, TargetDir=C:\\Python312, no PATH modification")
    return False


def create_venv() -> bool:
    """Create .venv312 if it does not already exist."""
    if VENV_DIR.exists():
        print("Venv exists: " + str(VENV_DIR))
        return True
    return run([str(PY312), "-m", "venv", str(VENV_DIR)], "create venv")


def install_packages() -> bool:
    """Install all required packages into .venv312."""
    steps = [
        ([str(PYTHON), "-m", "pip", "install", "--upgrade", "pip"], "upgrade pip"),
        ([str(PIP), "install", "numba", "numpy", "pandas", "streamlit", "plotly", "pyarrow"], "core"),
        ([str(PIP), "install", "scikit-learn", "scipy", "requests", "pyyaml"], "utils"),
        ([str(PIP), "install", "reportlab"], "pdf"),
        (
            [str(PIP), "install", "torch", "torchvision",
             "--index-url", "https://download.pytorch.org/whl/cu130"],
            "torch+cuda",
        ),
    ]
    for cmd, label in steps:
        if not run(cmd, label):
            return False
    return True


def verify_imports() -> bool:
    """Verify key imports work in the new venv."""
    checks = [
        "import numba; print('numba', numba.__version__)",
        "import streamlit; print('streamlit', streamlit.__version__)",
        "import pandas; print('pandas', pandas.__version__)",
        "import plotly; print('plotly', plotly.__version__)",
        "import numpy; print('numpy', numpy.__version__)",
    ]
    ok = True
    for check in checks:
        result = subprocess.run([str(PYTHON), "-c", check], capture_output=True, text=True)
        if result.returncode == 0:
            print("  PASS: " + result.stdout.strip())
        else:
            print("  FAIL: " + check)
            print("        " + result.stderr.strip())
            ok = False
    return ok


def verify_cuda() -> None:
    """Check numba CUDA availability (informational only, not a hard failure)."""
    code = (
        "from numba import cuda\n"
        "avail = cuda.is_available()\n"
        "print('CUDA available:', avail)\n"
        "if avail:\n"
        "    dev = cuda.get_current_device()\n"
        "    name = dev.name\n"
        "    if isinstance(name, bytes): name = name.decode()\n"
        "    print('Device:', name)\n"
        "    free, total = cuda.current_context().get_memory_info()\n"
        "    print('VRAM: {:.1f} GB free / {:.1f} GB total'.format(free/1024**3, total/1024**3))\n"
    )
    result = subprocess.run([str(PYTHON), "-c", code], capture_output=True, text=True)
    print(result.stdout.strip())
    if result.returncode != 0:
        print("CUDA check failed (non-fatal):", result.stderr.strip()[:200])


def verify_backtester() -> bool:
    """Verify backtester engine and signals import cleanly."""
    code = (
        "import sys\n"
        "sys.path.insert(0, r'" + str(ROOT).replace("\\", "/") + "')\n"
        "from engine.backtester_55_89 import Backtester5589\n"
        "from signals.ema_cross_55_89 import compute_signals_55_89\n"
        "print('backtester_55_89 OK')\n"
        "print('ema_cross_55_89 OK')\n"
    )
    result = subprocess.run([str(PYTHON), "-c", code], capture_output=True, text=True)
    print(result.stdout.strip())
    if result.returncode != 0:
        print("FAIL:", result.stderr.strip()[:300])
        return False
    return True


def print_run_commands() -> None:
    """Print activation and dashboard run commands for the user."""
    activate = str(VENV_DIR / "Scripts" / "Activate.ps1")
    dashboard = str(ROOT / "scripts" / "dashboard_55_89_v3.py")
    print("")
    print("=== DONE ===")
    print("Activate venv (PowerShell):")
    print("  & \"" + activate + "\"")
    print("")
    print("Run dashboard:")
    print("  streamlit run \"" + dashboard + "\"")
    print("")
    print("Or full path (no activate needed):")
    print("  & \"" + str(PYTHON) + "\" -m streamlit run \"" + dashboard + "\"")


def main() -> None:
    """Run full venv setup: create, install, verify."""
    print("=== setup_venv312.py ===")
    print("Root:     " + str(ROOT))
    print("Venv dir: " + str(VENV_DIR))
    print("")

    if not check_python312():
        sys.exit(1)

    print("")
    print("=== Step 1: Create venv ===")
    if not create_venv():
        sys.exit(1)

    print("")
    print("=== Step 2: Install packages ===")
    if not install_packages():
        sys.exit(1)

    print("")
    print("=== Step 3: Verify imports ===")
    if not verify_imports():
        sys.exit(1)

    print("")
    print("=== Step 4: CUDA check ===")
    verify_cuda()

    print("")
    print("=== Step 5: Backtester imports ===")
    verify_backtester()

    print_run_commands()


if __name__ == "__main__":
    main()
