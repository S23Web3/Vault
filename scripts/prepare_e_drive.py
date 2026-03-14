"""
Master E: drive preparation script.

Runs two phases in sequence:
  Phase 1 — Migrate all vault files modified since 2026-01-19 to E:/Obsidian Vault/
  Phase 2 — Export pip packages (requirements + wheels) to E:/pip-packages/

Everything ends up on E: including this script itself.
Originals on C: are NOT deleted — review the log first, delete manually when satisfied.

Run: python "C:/Users/User/Documents/Obsidian Vault/scripts/prepare_e_drive.py"
"""
import os
import shutil
import subprocess
import sys
import logging
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SOURCE_ROOT   = Path(r"C:\Users\User\Documents\Obsidian Vault")
DEST_ROOT     = Path(r"E:\Obsidian Vault")
LOG_PATH      = Path(r"E:\migration-log-" + datetime.now().strftime("%Y-%m-%d") + ".txt")
CUTOFF_DT     = datetime(2026, 1, 19, 0, 0, 0)
CUTOFF_TS     = CUTOFF_DT.timestamp()
PROGRESS_EVERY = 50

PROJECTS_ROOT = SOURCE_ROOT / "PROJECTS"
PIP_EXPORT_DIR = Path(r"E:\pip-packages")
VENV_PATTERNS  = [".venv", ".venv312", "venv", ".venv311", ".venv310", "env"]

SKIP_DIRS = {
    ".git", "__pycache__", "venv", "env", ".venv",
    ".venv312", ".venv311", ".venv310",
    "node_modules", ".mypy_cache",
}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
def setup_logging() -> logging.Logger:
    """Set up dual-handler logger writing to E: and console."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    fmt     = "%(asctime)s [%(levelname)s] %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    logger  = logging.getLogger("prepare_e")
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler(str(LOG_PATH), encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(fmt, datefmt=datefmt))

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(fmt, datefmt=datefmt))

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


# ---------------------------------------------------------------------------
# Phase 1 — File migration
# ---------------------------------------------------------------------------
def should_skip_dir(name: str) -> bool:
    """Return True if directory should be excluded from traversal."""
    return name in SKIP_DIRS


def copy_file(src: Path, dst: Path, log: logging.Logger) -> tuple:
    """
    Copy src to dst preserving timestamps. Skip if dst exists with same size.
    Returns (success: bool, skipped: bool).
    """
    try:
        src_size = src.stat().st_size
        if dst.exists() and dst.stat().st_size == src_size:
            log.debug("[SKIP] %s (already exists, same size)", src.name)
            return True, True
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src), str(dst))
        if dst.stat().st_size != src_size:
            log.error("SIZE MISMATCH %s", src)
            return False, False
        log.debug("[OK] %s (%d bytes)", src.name, src_size)
        return True, False
    except Exception as exc:
        log.error("[FAIL] %s: %s", src, exc)
        return False, False


def collect_files(source: Path, log: logging.Logger) -> list:
    """Walk source tree and return files modified on or after CUTOFF_TS."""
    candidates = []
    for root_str, dirs, files in os.walk(str(source)):
        dirs[:] = [d for d in dirs if not should_skip_dir(d)]
        root = Path(root_str)
        for fname in files:
            fpath = root / fname
            try:
                if fpath.stat().st_mtime >= CUTOFF_TS:
                    candidates.append(fpath)
            except OSError as exc:
                log.warning("STAT FAIL %s: %s", fpath, exc)
    return candidates


def run_migration(log: logging.Logger) -> bool:
    """Phase 1: copy vault files to E:. Return True if zero failures."""
    log.info("")
    log.info("=" * 70)
    log.info("PHASE 1 — FILE MIGRATION")
    log.info("Source : %s", SOURCE_ROOT)
    log.info("Dest   : %s", DEST_ROOT)
    log.info("Cutoff : %s", CUTOFF_DT.strftime("%Y-%m-%d"))
    log.info("=" * 70)

    log.info("Scanning source tree (skipping venvs, .git, __pycache__)...")
    files = collect_files(SOURCE_ROOT, log)
    total = len(files)
    log.info("Found %d files to migrate", total)

    if total == 0:
        log.info("Nothing to copy.")
        return True

    total_bytes = sum(f.stat().st_size for f in files if f.exists())
    log.info("Estimated size: %.1f MB", total_bytes / 1_048_576)

    ok_count = skip_count = fail_count = ok_bytes = 0
    for i, src in enumerate(files, 1):
        dst = DEST_ROOT / src.relative_to(SOURCE_ROOT)
        success, skipped = copy_file(src, dst, log)
        if success:
            if skipped:
                skip_count += 1
            else:
                ok_count += 1
                ok_bytes += src.stat().st_size
        else:
            fail_count += 1

        if i % PROGRESS_EVERY == 0 or i == total:
            log.info("Progress: %d / %d (%.0f%%)  COPIED=%d  SKIPPED=%d  FAIL=%d",
                     i, total, i / total * 100, ok_count, skip_count, fail_count)

    log.info("")
    log.info("Migration complete — COPIED=%d (%.1f MB)  SKIPPED=%d  FAIL=%d",
             ok_count, ok_bytes / 1_048_576, skip_count, fail_count)
    return fail_count == 0


# ---------------------------------------------------------------------------
# Phase 2 — Pip package export
# ---------------------------------------------------------------------------
def find_venvs(log: logging.Logger) -> list:
    """Find all venvs under PROJECTS_ROOT. Return list of (name, pip_exe)."""
    found = []
    if not PROJECTS_ROOT.exists():
        log.error("PROJECTS_ROOT not found: %s", PROJECTS_ROOT)
        return found
    for project_dir in sorted(PROJECTS_ROOT.iterdir()):
        if not project_dir.is_dir():
            continue
        for vname in VENV_PATTERNS:
            pip_exe = project_dir / vname / "Scripts" / "pip.exe"
            if pip_exe.exists():
                found.append((project_dir.name, pip_exe))
                log.info("Found venv: %s (%s)", project_dir.name, vname)
    return found


def export_requirements(pip_exe: Path, out_file: Path, log: logging.Logger) -> bool:
    """Run pip freeze and save to out_file. Return True on success."""
    try:
        r = subprocess.run([str(pip_exe), "freeze"],
                           capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            log.error("pip freeze failed: %s", r.stderr.strip())
            return False
        out_file.write_text(r.stdout, encoding="utf-8")
        count = len([l for l in r.stdout.splitlines() if l.strip()])
        log.info("Exported %d packages -> %s", count, out_file.name)
        return True
    except Exception as exc:
        log.error("pip freeze error: %s", exc)
        return False


def download_packages(pip_exe: Path, req_file: Path, dest_dir: Path, log: logging.Logger) -> bool:
    """Download all wheels/sdists from req_file into dest_dir. Return True on success."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    log.info("Downloading wheels to %s ...", dest_dir)
    try:
        r = subprocess.run(
            [str(pip_exe), "download", "-r", str(req_file), "-d", str(dest_dir)],
            capture_output=True, text=True, timeout=900
        )
        if r.returncode != 0:
            log.error("pip download failed: %s", r.stderr.strip())
            return False
        log.info("Download complete")
        return True
    except subprocess.TimeoutExpired:
        log.error("pip download timed out")
        return False
    except Exception as exc:
        log.error("pip download error: %s", exc)
        return False


def write_bat(export_dir: Path, req_files: list) -> None:
    """Write install_packages.bat for Windows target."""
    lines = [
        "@echo off",
        "REM Install pip packages from local files — no internet needed",
        "REM Generated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "REM Copy this entire folder to the target device and run this file.",
        "",
        "echo Installing packages from local files...",
        "",
    ]
    for req_name in req_files:
        pkg = req_name.replace("requirements-", "").replace(".txt", "")
        lines.append("echo --- " + pkg + " ---")
        lines.append(
            'pip install --no-index --find-links "%~dp0packages-' + pkg + '" -r "%~dp0' + req_name + '"'
        )
        lines.append('if %ERRORLEVEL% NEQ 0 echo [WARN] Some packages failed for ' + pkg)
        lines.append("")
    lines += ["echo.", "echo Done.", "pause"]
    bat = export_dir / "install_packages.bat"
    bat.write_text("\r\n".join(lines), encoding="utf-8")


def write_sh(export_dir: Path, req_files: list) -> None:
    """Write install_packages.sh for Linux/Mac target."""
    lines = [
        "#!/bin/bash",
        "# Install pip packages from local files — no internet needed",
        "# Generated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"',
        "",
    ]
    for req_name in req_files:
        pkg = req_name.replace("requirements-", "").replace(".txt", "")
        lines.append('echo "--- ' + pkg + ' ---"')
        lines.append(
            'pip install --no-index --find-links "$SCRIPT_DIR/packages-' + pkg + '" -r "$SCRIPT_DIR/' + req_name + '"'
        )
        lines.append("")
    lines.append('echo "Done."')
    sh = export_dir / "install_packages.sh"
    sh.write_text("\n".join(lines), encoding="utf-8")


def run_pip_export(log: logging.Logger) -> None:
    """Phase 2: export requirements and download wheels to E:/pip-packages/."""
    log.info("")
    log.info("=" * 70)
    log.info("PHASE 2 — PIP PACKAGE EXPORT")
    log.info("Export dir: %s", PIP_EXPORT_DIR)
    log.info("=" * 70)

    PIP_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    venvs = find_venvs(log)

    if not venvs:
        log.warning("No venvs found — skipping pip export")
        return

    req_files = []
    for project_name, pip_exe in venvs:
        log.info("")
        log.info("--- %s ---", project_name)
        req_name = "requirements-" + project_name + ".txt"
        req_path = PIP_EXPORT_DIR / req_name
        pkg_dir  = PIP_EXPORT_DIR / ("packages-" + project_name)

        if not export_requirements(pip_exe, req_path, log):
            log.error("Skipping %s", project_name)
            continue

        download_packages(pip_exe, req_path, pkg_dir, log)
        req_files.append(req_name)

    if not req_files:
        log.error("Nothing exported")
        return

    write_bat(PIP_EXPORT_DIR, req_files)
    write_sh(PIP_EXPORT_DIR, req_files)
    log.info("Install scripts written to %s", PIP_EXPORT_DIR)


# ---------------------------------------------------------------------------
# Copy this script to E:
# ---------------------------------------------------------------------------
def copy_self(log: logging.Logger) -> None:
    """Copy this script to E: so it is self-contained on the drive."""
    this = Path(__file__).resolve()
    dst  = Path(r"E:\prepare_e_drive.py")
    try:
        shutil.copy2(str(this), str(dst))
        log.info("Script copied to %s", dst)
    except Exception as exc:
        log.warning("Could not copy script to E: — %s", exc)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    """Run Phase 1 (migrate files) then Phase 2 (export pip packages)."""
    log = setup_logging()
    start = datetime.now()

    log.info("")
    log.info("##############################################################")
    log.info("  E: DRIVE PREPARATION — %s", start.strftime("%Y-%m-%d %H:%M:%S"))
    log.info("##############################################################")

    migration_ok = run_migration(log)
    run_pip_export(log)
    copy_self(log)

    elapsed = (datetime.now() - start).seconds
    log.info("")
    log.info("##############################################################")
    log.info("  ALL DONE  —  elapsed %dm %ds", elapsed // 60, elapsed % 60)
    log.info("  Migration OK : %s", "YES" if migration_ok else "CHECK LOG FOR FAILURES")
    log.info("  E: drive     : %s", Path("E:/").resolve())
    log.info("  Full log     : %s", LOG_PATH)
    log.info("##############################################################")
    log.info("")
    log.info("Next steps:")
    log.info("  1. Check log for [FAIL] entries")
    log.info("  2. When satisfied, manually delete originals from C:")
    log.info("  3. On target device: run E:/pip-packages/install_packages.bat")


if __name__ == "__main__":
    main()
