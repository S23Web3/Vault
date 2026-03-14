"""
Migration script: copy all files modified since 2026-01-19 from Obsidian Vault to E: drive.
Mirrors the original folder structure. Keeps originals on C: intact.
Writes a timestamped log to E:/migration-log-2026-03-14.txt.

Run: python "C:/Users/User/Documents/Obsidian Vault/scripts/migrate_to_e_drive.py"
"""
import os
import sys
import shutil
import logging
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SOURCE_ROOT = Path(r"C:\Users\User\Documents\Obsidian Vault")
DEST_ROOT   = Path(r"E:\Obsidian Vault")
LOG_PATH    = Path(r"E:\migration-log-2026-03-14.txt")
CUTOFF_DT   = datetime(2026, 1, 19, 0, 0, 0)
CUTOFF_TS   = CUTOFF_DT.timestamp()

SKIP_DIRS = {".git", "__pycache__", "venv", "env", ".venv", "node_modules", ".mypy_cache"}
PROGRESS_EVERY = 50

# ---------------------------------------------------------------------------
# Logging — dual: file on E: + console
# ---------------------------------------------------------------------------
def setup_logging() -> logging.Logger:
    """Set up dual-handler logger (console + E:/migration-log file)."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    fmt = "%(asctime)s [%(levelname)s] %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    logger = logging.getLogger("migrate")
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
# Core
# ---------------------------------------------------------------------------
def should_skip_dir(name: str) -> bool:
    """Return True if this directory name should be excluded from traversal."""
    return name in SKIP_DIRS


def copy_file(src: Path, dst: Path, log: logging.Logger) -> bool:
    """
    Copy src to dst with shutil.copy2 (preserves timestamps).
    Verify by comparing file sizes. Return True on success.
    """
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src), str(dst))
        src_size = src.stat().st_size
        dst_size = dst.stat().st_size
        if src_size != dst_size:
            log.error("SIZE MISMATCH [%d != %d] %s", src_size, dst_size, src)
            return False
        log.debug("[OK] %s -> %s (%d bytes)", src, dst, src_size)
        return True
    except Exception as exc:
        log.error("[FAIL] %s: %s", src, exc)
        return False


def collect_files(source: Path, log: logging.Logger) -> list:
    """
    Walk source tree, return list of Path objects modified on or after CUTOFF_TS.
    Skips SKIP_DIRS directories.
    """
    candidates = []
    for root_str, dirs, files in os.walk(str(source)):
        # Prune skipped directories in-place so os.walk won't descend into them
        dirs[:] = [d for d in dirs if not should_skip_dir(d)]
        root = Path(root_str)
        for fname in files:
            fpath = root / fname
            try:
                mtime = fpath.stat().st_mtime
                if mtime >= CUTOFF_TS:
                    candidates.append(fpath)
            except OSError as exc:
                log.warning("STAT FAIL %s: %s", fpath, exc)
    return candidates


def main() -> None:
    """Entry point: collect, copy, verify, summarise."""
    log = setup_logging()

    log.info("=" * 70)
    log.info("Migration start")
    log.info("Source : %s", SOURCE_ROOT)
    log.info("Dest   : %s", DEST_ROOT)
    log.info("Cutoff : %s (files modified on or after this date)", CUTOFF_DT.strftime("%Y-%m-%d"))
    log.info("Log    : %s", LOG_PATH)
    log.info("=" * 70)

    # --- Phase 1: collect ---
    log.info("Scanning source tree...")
    files = collect_files(SOURCE_ROOT, log)
    total = len(files)
    log.info("Found %d files modified since %s", total, CUTOFF_DT.date())

    if total == 0:
        log.info("Nothing to copy. Exiting.")
        return

    # Estimate total size
    total_bytes = 0
    for f in files:
        try:
            total_bytes += f.stat().st_size
        except OSError:
            pass
    log.info("Estimated total size: %.1f MB", total_bytes / 1_048_576)
    log.info("")

    # --- Phase 2: copy ---
    ok_count = 0
    fail_count = 0
    ok_bytes = 0

    for i, src in enumerate(files, 1):
        rel = src.relative_to(SOURCE_ROOT)
        dst = DEST_ROOT / rel
        success = copy_file(src, dst, log)
        if success:
            ok_count += 1
            try:
                ok_bytes += src.stat().st_size
            except OSError:
                pass
        else:
            fail_count += 1

        if i % PROGRESS_EVERY == 0 or i == total:
            pct = i / total * 100
            log.info("Progress: %d / %d (%.0f%%)  OK=%d  FAIL=%d", i, total, pct, ok_count, fail_count)

    # --- Phase 3: summary ---
    log.info("")
    log.info("=" * 70)
    log.info("MIGRATION COMPLETE")
    log.info("Total files scanned : %d", total)
    log.info("Copied OK           : %d (%.1f MB)", ok_count, ok_bytes / 1_048_576)
    log.info("Failed              : %d", fail_count)
    log.info("Destination         : %s", DEST_ROOT)
    log.info("Log saved to        : %s", LOG_PATH)
    log.info("")
    if fail_count == 0:
        log.info("All files copied successfully.")
        log.info("Review the log, then manually delete originals from C: when satisfied.")
    else:
        log.warning("%d file(s) failed to copy. Search log for [FAIL] to review.", fail_count)
    log.info("=" * 70)


if __name__ == "__main__":
    main()
