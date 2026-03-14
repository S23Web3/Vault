"""
Export pip packages for offline installation on another device.

What this does:
1. Exports requirements.txt from each venv found in PROJECTS/
2. Downloads all .whl/.tar.gz files into E:/pip-packages/
3. Generates an install script (install_packages.bat) for the target device

On the target device:
  1. Copy E:/pip-packages/ folder over
  2. Run: install_packages.bat
  That's it - all packages install from local files, no internet needed.

Run: python "C:/Users/User/Documents/Obsidian Vault/scripts/export_pip_packages.py"
"""
import shutil
import subprocess
import sys
import logging
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
PROJECTS_ROOT = Path(r"C:\Users\User\Documents\Obsidian Vault\PROJECTS")
EXPORT_DIR = Path(r"E:\pip-packages")
LOG_FMT = "%(asctime)s [%(levelname)s] %(message)s"
LOG_DATEFMT = "%Y-%m-%d %H:%M:%S"

# Known venv directory name patterns
VENV_PATTERNS = [".venv", ".venv312", "venv", ".venv311", ".venv310", "env"]

logging.basicConfig(level=logging.INFO, format=LOG_FMT, datefmt=LOG_DATEFMT)
log = logging.getLogger("export_pip")


def find_venvs(projects_root: Path) -> list:
    """Scan each project dir for known venv folder names. Return list of (project_name, venv_path, pip_path)."""
    found = []
    if not projects_root.exists():
        log.error("PROJECTS_ROOT does not exist: %s", projects_root)
        return found

    for project_dir in sorted(projects_root.iterdir()):
        if not project_dir.is_dir():
            continue
        for vname in VENV_PATTERNS:
            venv_path = project_dir / vname
            pip_exe = venv_path / "Scripts" / "pip.exe"
            if pip_exe.exists():
                found.append((project_dir.name, venv_path, pip_exe))
                log.info("Found venv: %s -> %s", project_dir.name, venv_path)
    return found


def export_requirements(pip_exe: Path, output_file: Path) -> bool:
    """Run pip freeze and write to output_file. Return True on success."""
    try:
        result = subprocess.run(
            [str(pip_exe), "freeze"],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            log.error("pip freeze failed: %s", result.stderr.strip())
            return False
        output_file.write_text(result.stdout, encoding="utf-8")
        line_count = len([l for l in result.stdout.strip().splitlines() if l.strip()])
        log.info("Wrote %d packages to %s", line_count, output_file)
        return True
    except Exception as exc:
        log.error("Failed to export requirements: %s", exc)
        return False


def download_packages(pip_exe: Path, req_file: Path, dest_dir: Path) -> bool:
    """Download all packages from requirements file as wheels/sdists into dest_dir."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    log.info("Downloading packages to %s ...", dest_dir)
    try:
        result = subprocess.run(
            [str(pip_exe), "download", "-r", str(req_file), "-d", str(dest_dir)],
            capture_output=True, text=True, timeout=600
        )
        if result.returncode != 0:
            log.error("pip download failed:\n%s", result.stderr.strip())
            # Print stdout too — pip sometimes puts errors there
            if result.stdout.strip():
                log.error("stdout:\n%s", result.stdout.strip())
            return False
        log.info("Download complete")
        return True
    except subprocess.TimeoutExpired:
        log.error("pip download timed out after 600s")
        return False
    except Exception as exc:
        log.error("Download failed: %s", exc)
        return False


def write_install_script(export_dir: Path, req_files: list) -> None:
    """Generate install_packages.bat for the target device."""
    bat_path = export_dir / "install_packages.bat"
    lines = [
        "@echo off",
        "REM ============================================================",
        "REM Install all pip packages from local files (no internet needed)",
        "REM Generated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "REM",
        "REM Usage: copy this entire folder to the target device,",
        "REM        then run this .bat from inside the folder.",
        "REM ============================================================",
        "",
        "echo.",
        'echo Installing packages from local files...',
        "echo.",
        "",
    ]
    for req_name in req_files:
        pkg_subdir = req_name.replace("requirements-", "").replace(".txt", "")
        lines.append(
            f'echo Installing packages for: {pkg_subdir}'
        )
        lines.append(
            f'pip install --no-index --find-links "%~dp0packages-{pkg_subdir}" '
            f'-r "%~dp0{req_name}"'
        )
        lines.append(
            f'if %ERRORLEVEL% NEQ 0 echo [WARN] Some packages for {pkg_subdir} failed to install'
        )
        lines.append("")

    lines.append("echo.")
    lines.append("echo Done. Check output above for any errors.")
    lines.append("pause")

    bat_path.write_text("\r\n".join(lines), encoding="utf-8")
    log.info("Install script written: %s", bat_path)


def write_install_script_sh(export_dir: Path, req_files: list) -> None:
    """Generate install_packages.sh for Linux/Mac targets."""
    sh_path = export_dir / "install_packages.sh"
    lines = [
        "#!/bin/bash",
        "# ============================================================",
        "# Install all pip packages from local files (no internet needed)",
        "# Generated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "#",
        "# Usage: copy this entire folder to the target device,",
        "#        then run: bash install_packages.sh",
        "# ============================================================",
        "",
        'SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"',
        "",
    ]
    for req_name in req_files:
        pkg_subdir = req_name.replace("requirements-", "").replace(".txt", "")
        lines.append(f'echo "Installing packages for: {pkg_subdir}"')
        lines.append(
            f'pip install --no-index --find-links "$SCRIPT_DIR/packages-{pkg_subdir}" '
            f'-r "$SCRIPT_DIR/{req_name}"'
        )
        lines.append("")

    lines.append('echo "Done."')

    sh_path.write_text("\n".join(lines), encoding="utf-8")
    log.info("Install script written: %s", sh_path)


def main() -> None:
    """Entry point: find venvs, export requirements, download packages, write install scripts."""
    log.info("=" * 60)
    log.info("Pip Package Exporter")
    log.info("Export dir: %s", EXPORT_DIR)
    log.info("=" * 60)

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    venvs = find_venvs(PROJECTS_ROOT)
    if not venvs:
        log.warning("No venvs found under %s", PROJECTS_ROOT)
        return

    req_files = []
    for project_name, venv_path, pip_exe in venvs:
        log.info("")
        log.info("--- Project: %s ---", project_name)

        req_name = f"requirements-{project_name}.txt"
        req_path = EXPORT_DIR / req_name
        pkg_dir = EXPORT_DIR / f"packages-{project_name}"

        # Step 1: export requirements
        if not export_requirements(pip_exe, req_path):
            log.error("Skipping %s — could not export requirements", project_name)
            continue

        # Step 2: download packages
        if not download_packages(pip_exe, req_path, pkg_dir):
            log.warning("Package download had errors for %s — check log above", project_name)
            # Still include in install script — partial installs are better than none

        req_files.append(req_name)

    if not req_files:
        log.error("No requirements exported. Nothing to do.")
        return

    # Step 3: copy this script itself to E: so it's self-contained
    this_script = Path(__file__).resolve()
    script_copy = EXPORT_DIR / this_script.name
    try:
        shutil.copy2(str(this_script), str(script_copy))
        log.info("Script copied to: %s", script_copy)
    except Exception as exc:
        log.warning("Could not copy script to E: — %s", exc)

    # Step 4: write install scripts (Windows + Linux/Mac)
    write_install_script(EXPORT_DIR, req_files)
    write_install_script_sh(EXPORT_DIR, req_files)

    log.info("")
    log.info("=" * 60)
    log.info("EXPORT COMPLETE")
    log.info("Location    : %s", EXPORT_DIR)
    log.info("Projects    : %d", len(req_files))
    log.info("")
    log.info("To install on another device:")
    log.info("  1. Copy the entire %s folder to the target", EXPORT_DIR.name)
    log.info("  2. Windows: run install_packages.bat")
    log.info("  3. Linux  : run bash install_packages.sh")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
