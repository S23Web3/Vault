"""
Milestone end-of-day push script.
1. Copies all vault files modified today to E:/Obsidian Vault/ (skip-existing)
2. Stages all untracked/modified files in git
3. Commits with a timestamped message
4. Pushes to origin main

Run: python "C:/Users/User/Documents/Obsidian Vault/scripts/milestone_push.py"
Run with custom message: python "C:/Users/User/Documents/Obsidian Vault/scripts/milestone_push.py" -m "my message"
Dry run (no git commit/push): python "C:/Users/User/Documents/Obsidian Vault/scripts/milestone_push.py" --dry-run
Install daily 9pm task: python "C:/Users/User/Documents/Obsidian Vault/scripts/milestone_push.py" --install
Remove daily task: python "C:/Users/User/Documents/Obsidian Vault/scripts/milestone_push.py" --uninstall
"""
import os
import sys
import shutil
import logging
import argparse
import subprocess
from datetime import datetime, date
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
VAULT_ROOT  = Path(r"C:\Users\User\Documents\Obsidian Vault")
DEST_ROOT   = Path(r"E:\Obsidian Vault")
LOG_PATH    = Path(r"E:\milestone-push.log") if Path(r"E:\\").exists() else Path(r"C:\Users\User\Documents\Obsidian Vault\logs\milestone-push.log")
TODAY_TS    = datetime.combine(date.today(), datetime.min.time()).timestamp()
PROGRESS_EVERY = 100

SKIP_DIRS = {
    ".git", "__pycache__", "venv", "env", ".venv",
    ".venv312", ".venv311", ".venv310",
    "node_modules", ".mypy_cache",
}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
def setup_logging() -> logging.Logger:
    """Set up dual-handler logger (console + E:/milestone-push.log)."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    fmt     = "%(asctime)s [%(levelname)s] %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    logger  = logging.getLogger("milestone")
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler(str(LOG_PATH), encoding="utf-8", mode="a")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(fmt, datefmt=datefmt))

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(fmt, datefmt=datefmt))

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


# ---------------------------------------------------------------------------
# Phase 1 — sync today's files to E:
# ---------------------------------------------------------------------------
def should_skip(name: str) -> bool:
    """Return True if directory should be skipped."""
    return name in SKIP_DIRS


def sync_to_e(log: logging.Logger, dry_run: bool) -> tuple:
    """Copy files modified today to E:, skip if already same size. Return (copied, skipped, failed)."""
    log.info("Scanning for files modified today (%s)...", date.today())
    copied = skipped = failed = 0

    for root_str, dirs, files in os.walk(str(VAULT_ROOT)):
        dirs[:] = [d for d in dirs if not should_skip(d)]
        root = Path(root_str)
        for fname in files:
            src = root / fname
            try:
                if src.stat().st_mtime < TODAY_TS:
                    continue
                src_size = src.stat().st_size
                dst = DEST_ROOT / src.relative_to(VAULT_ROOT)

                if dst.exists() and dst.stat().st_size == src_size:
                    skipped += 1
                    continue

                if dry_run:
                    log.info("[DRY] Would copy: %s", src.relative_to(VAULT_ROOT))
                    copied += 1
                    continue

                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src), str(dst))
                copied += 1

                total = copied + skipped + failed
                if total % PROGRESS_EVERY == 0:
                    log.info("E: sync progress — copied=%d skipped=%d failed=%d", copied, skipped, failed)

            except Exception as exc:
                log.error("[FAIL] %s: %s", src, exc)
                failed += 1

    return copied, skipped, failed


# ---------------------------------------------------------------------------
# Phase 2 — git commit + push
# ---------------------------------------------------------------------------
def git_run(args: list, log: logging.Logger) -> tuple:
    """Run a git command in VAULT_ROOT. Return (returncode, stdout, stderr)."""
    result = subprocess.run(
        ["git"] + args,
        cwd=str(VAULT_ROOT),
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def git_status(log: logging.Logger) -> list:
    """Return list of untracked/modified file paths."""
    rc, out, err = git_run(["status", "--short"], log)
    if rc != 0:
        log.error("git status failed: %s", err)
        return []
    lines = [l for l in out.splitlines() if l.strip()]
    return lines


def git_commit_push(message: str, log: logging.Logger, dry_run: bool) -> bool:
    """Stage all changes, commit, and push. Return True on success."""

    # Check status
    changes = git_status(log)
    if not changes:
        log.info("No git changes to commit")
        return True

    log.info("Git changes: %d files", len(changes))
    for line in changes[:20]:
        log.info("  %s", line)
    if len(changes) > 20:
        log.info("  ... and %d more", len(changes) - 20)

    if dry_run:
        log.info("[DRY] Would commit %d files: %s", len(changes), message)
        return True

    # Stage all
    rc, out, err = git_run(["add", "-A"], log)
    if rc != 0:
        log.error("git add failed: %s", err)
        return False
    log.info("Staged %d changes", len(changes))

    # Commit
    rc, out, err = git_run(["commit", "-m", message], log)
    if rc != 0:
        log.error("git commit failed: %s", err)
        return False
    log.info("Committed: %s", message)

    # Push
    log.info("Pushing to origin main...")
    rc, out, err = git_run(["push", "origin", "main"], log)
    if rc != 0:
        log.error("git push failed: %s", err)
        log.error(err)
        return False
    log.info("Pushed successfully")
    return True


# ---------------------------------------------------------------------------
# Scheduled task install/uninstall
# ---------------------------------------------------------------------------
def install_task() -> None:
    """Register MilestonePush as a daily scheduled task at 21:00."""
    script = Path(__file__).resolve()
    python = Path(sys.executable).resolve()
    start  = datetime.now().strftime("%Y-%m-%dT") + "21:00:00"

    task_xml = (
        '<?xml version="1.0" encoding="UTF-16"?>'
        '<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">'
        '<RegistrationInfo><Description>Vault milestone push — daily 9pm backup to E: and git</Description></RegistrationInfo>'
        '<Triggers>'
        '<CalendarTrigger>'
        '<StartBoundary>' + start + '</StartBoundary>'
        '<Enabled>true</Enabled>'
        '<ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay>'
        '</CalendarTrigger>'
        '</Triggers>'
        '<Principals><Principal><LogonType>InteractiveToken</LogonType><RunLevel>HighestAvailable</RunLevel></Principal></Principals>'
        '<Settings>'
        '<MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>'
        '<DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>'
        '<StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>'
        '<RunOnlyIfNetworkAvailable>true</RunOnlyIfNetworkAvailable>'
        '<ExecutionTimeLimit>PT2H</ExecutionTimeLimit>'
        '<Hidden>true</Hidden>'
        '</Settings>'
        '<Actions><Exec>'
        '<Command>' + str(python) + '</Command>'
        '<Arguments>"' + str(script) + '"</Arguments>'
        '</Exec></Actions>'
        '</Task>'
    )

    xml_path = Path(r"C:\Users\User\AppData\Local\Temp\milestone-task.xml")
    xml_path.write_text(task_xml, encoding="utf-16")

    result = subprocess.run(
        ["schtasks", "/create", "/tn", "MilestonePush", "/xml", str(xml_path), "/f"],
        capture_output=True, text=True
    )
    xml_path.unlink(missing_ok=True)

    log = logging.getLogger("milestone")
    if result.returncode == 0:
        log.info("Task 'MilestonePush' registered — runs daily at 21:00")
        log.info("Syncs today's files to E: and pushes to git automatically")
    else:
        log.error("Task registration failed: %s", result.stderr.strip())


def uninstall_task() -> None:
    """Remove the MilestonePush scheduled task."""
    log = logging.getLogger("milestone")
    result = subprocess.run(
        ["schtasks", "/delete", "/tn", "MilestonePush", "/f"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        log.info("Task 'MilestonePush' removed")
    else:
        log.error("Could not remove task: %s", result.stderr.strip())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    """Run E: sync then git commit+push."""
    parser = argparse.ArgumentParser(description="Milestone end-of-day push")
    parser.add_argument("-m", "--message", default="", help="Custom commit message")
    parser.add_argument("--dry-run",   action="store_true", help="Preview only — no writes or commits")
    parser.add_argument("--e-only",    action="store_true", help="Sync to E: only, skip git")
    parser.add_argument("--git-only",  action="store_true", help="Git commit+push only, skip E: sync")
    parser.add_argument("--install",   action="store_true", help="Install daily 9pm scheduled task")
    parser.add_argument("--uninstall", action="store_true", help="Remove daily scheduled task")
    args = parser.parse_args()

    log = setup_logging()

    if args.install:
        install_task()
        return
    if args.uninstall:
        uninstall_task()
        return

    start = datetime.now()
    ts    = start.strftime("%Y-%m-%d %H:%M:%S")

    log.info("")
    log.info("=" * 60)
    log.info("MILESTONE PUSH — %s%s", ts, " [DRY RUN]" if args.dry_run else "")
    log.info("=" * 60)

    # Build commit message
    commit_msg = args.message if args.message else (
        "Vault update: milestone push " + start.strftime("%Y-%m-%d %H:%M")
    )

    e_ok  = True
    git_ok = True

    # Phase 1: sync to E:
    if not args.git_only:
        log.info("")
        log.info("--- Phase 1: Sync today's files to E: ---")
        if not Path(r"E:\\").exists():
            log.warning("E: drive not found — skipping E: sync (plug in drive and run --e-only later)")
            e_ok = True  # not a failure — drive is just absent
        else:
            copied, skipped, failed = sync_to_e(log, args.dry_run)
            log.info("E: sync done — copied=%d skipped=%d failed=%d", copied, skipped, failed)
            e_ok = failed == 0

    # Phase 2: git
    if not args.e_only:
        log.info("")
        log.info("--- Phase 2: Git commit + push ---")
        git_ok = git_commit_push(commit_msg, log, args.dry_run)

    # Summary
    elapsed = (datetime.now() - start).seconds
    log.info("")
    log.info("=" * 60)
    log.info("DONE — elapsed %dm %ds", elapsed // 60, elapsed % 60)
    log.info("E: sync : %s", "OK" if e_ok else "FAILED — check log")
    log.info("Git push: %s", "OK" if git_ok else "FAILED — check log")
    log.info("Log     : %s", LOG_PATH)
    log.info("=" * 60)

    if not e_ok or not git_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
