"""
Claude Desktop Brief — auto-generated daily summary (twice daily at 08:00 and 20:00).

Reads INDEX.md, PROJECT-STATUS.md, PRODUCT-BACKLOG.md and generates a single
consolidated brief at 06-CLAUDE-LOGS/CLAUDE-DESKTOP-BRIEF.md for Claude Desktop
to load at session start.

Run: python "C:\Users\User\Documents\Obsidian Vault\scripts\build_daily_brief.py"
Run with dry-run: python "C:\Users\User\Documents\Obsidian Vault\scripts\build_daily_brief.py" --dry-run
Install daily 08:00 + 20:00 task: python "..." --install
Remove task: python "..." --uninstall
"""
import os
import sys
import logging
import argparse
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
VAULT_ROOT      = Path(r"C:\Users\User\Documents\Obsidian Vault")
LOGS_DIR        = VAULT_ROOT / "06-CLAUDE-LOGS"
INDEX_PATH      = LOGS_DIR / "INDEX.md"
STATUS_PATH     = LOGS_DIR / "PROJECT-STATUS.md"
BACKLOG_PATH    = VAULT_ROOT / "PRODUCT-BACKLOG.md"
OUTPUT_PATH     = LOGS_DIR / "CLAUDE-DESKTOP-BRIEF.md"
LOG_PATH        = VAULT_ROOT / "logs" / "YYYY-MM-DD-brief.log"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
def setup_logging() -> logging.Logger:
    """Set up dual-handler logger (console + log file with date rotation)."""
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = VAULT_ROOT / "logs" / f"{today}-brief.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    fmt     = "%(asctime)s [%(levelname)s] %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    logger  = logging.getLogger("brief")
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler(str(log_file), encoding="utf-8", mode="a")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(fmt, datefmt=datefmt))

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(fmt, datefmt=datefmt))

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


# ---------------------------------------------------------------------------
# Parsing functions
# ---------------------------------------------------------------------------
def parse_index_last_7_days(log: logging.Logger) -> str:
    """Extract session summaries from INDEX.md for the last 7 days."""
    if not INDEX_PATH.exists():
        log.warning("INDEX.md not found")
        return "*(No session logs available)*"

    content = INDEX_PATH.read_text(encoding="utf-8")
    lines = content.split("\n")

    # Collect date headers and associated table rows
    today = datetime.now()
    cutoff = today - timedelta(days=7)

    sections = {}  # date_str -> list of table lines
    current_date = None
    in_table = False

    for line in lines:
        if line.startswith("### "):
            date_str = line[4:].strip()
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                if date_obj >= cutoff:
                    current_date = date_str
                    sections[current_date] = []
                    in_table = False
                else:
                    current_date = None
            except ValueError:
                current_date = None
                in_table = False
        elif current_date and line.startswith("|"):
            if "File" in line and "Summary" in line:
                in_table = True
            elif in_table:
                sections[current_date].append(line)

    # Build output: newest first
    if not sections:
        return "*(No sessions in last 7 days)*"

    sorted_dates = sorted(sections.keys(), reverse=True)
    result = []
    for date_str in sorted_dates:
        result.append(f"### {date_str}")
        result.append("")
        result.extend(sections[date_str])
        result.append("")

    return "\n".join(result).strip()


def parse_status_what_is_working(log: logging.Logger) -> str:
    """Extract 'What is done and working' table from PROJECT-STATUS.md."""
    if not STATUS_PATH.exists():
        log.warning("PROJECT-STATUS.md not found")
        return "*(Status not available)*"

    content = STATUS_PATH.read_text(encoding="utf-8")
    lines = content.split("\n")

    in_section = False
    result = []

    for i, line in enumerate(lines):
        if line.strip() == "## What is done and working":
            in_section = True
            continue

        if in_section:
            if line.startswith("## ") and not line.startswith("## What"):
                break
            if line.startswith("---"):
                break
            result.append(line)

    return "\n".join(result).strip()


def parse_status_open_decisions(log: logging.Logger) -> str:
    """Extract 'Open decisions' list from PROJECT-STATUS.md."""
    if not STATUS_PATH.exists():
        return "*(Open decisions not available)*"

    content = STATUS_PATH.read_text(encoding="utf-8")
    lines = content.split("\n")

    in_section = False
    result = []

    for line in lines:
        if line.strip() == "## Open decisions":
            in_section = True
            continue

        if in_section:
            if line.startswith("## "):
                break
            if line.startswith("---"):
                break
            result.append(line)

    return "\n".join(result).strip()


def parse_status_one_liner(log: logging.Logger) -> str:
    """Extract 'One-line summary' from PROJECT-STATUS.md (last non-empty line before EOF)."""
    if not STATUS_PATH.exists():
        return "*(Summary not available)*"

    content = STATUS_PATH.read_text(encoding="utf-8")
    lines = content.split("\n")

    in_section = False
    result = []

    for line in lines:
        if line.strip() == "## One-line summary":
            in_section = True
            continue

        if in_section:
            if line.startswith("## ") or line.startswith("---"):
                break
            result.append(line)

    text = "\n".join(result).strip()
    return text if text else "*(Summary not available)*"


def parse_backlog_p0(log: logging.Logger) -> str:
    """Extract P0 section from PRODUCT-BACKLOG.md."""
    if not BACKLOG_PATH.exists():
        log.warning("PRODUCT-BACKLOG.md not found")
        return "*(P0 Backlog not available)*"

    content = BACKLOG_PATH.read_text(encoding="utf-8")
    lines = content.split("\n")

    in_section = False
    result = []

    for line in lines:
        if line.strip() == "## P0 — Active / In Progress":
            in_section = True
            result.append(line)
            continue

        if in_section:
            if line.startswith("## P") and "P0" not in line:
                break
            result.append(line)

    return "\n".join(result).strip()


# ---------------------------------------------------------------------------
# Generate brief
# ---------------------------------------------------------------------------
def generate_brief(log: logging.Logger) -> str:
    """Assemble all sections into the final brief."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    sections = [
        "# Claude Desktop Brief",
        f"*Generated: {now}*",
        "",
        "## One-line project summary",
        parse_status_one_liner(log),
        "",
        "## Recent sessions (last 7 days)",
        parse_index_last_7_days(log),
        "",
        "## What is working",
        parse_status_what_is_working(log),
        "",
        "## P0 Backlog",
        parse_backlog_p0(log),
        "",
        "## Open decisions",
        parse_status_open_decisions(log),
    ]

    return "\n".join(sections)


# ---------------------------------------------------------------------------
# Write output
# ---------------------------------------------------------------------------
def write_brief(content: str, log: logging.Logger, dry_run: bool) -> bool:
    """Write brief to OUTPUT_PATH. Return True on success."""
    if dry_run:
        print(content)
        log.info("[DRY RUN] Would write to: %s", OUTPUT_PATH)
        return True

    try:
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.write_text(content, encoding="utf-8")
        log.info("Brief written: %s", OUTPUT_PATH)
        return True
    except Exception as exc:
        log.error("Failed to write brief: %s", exc)
        return False


# ---------------------------------------------------------------------------
# Scheduled task install/uninstall
# ---------------------------------------------------------------------------
def install_task() -> None:
    """Register ClaudeDesktopBrief as a daily scheduled task at 08:00 and 20:00."""
    script = Path(__file__).resolve()
    python = Path(sys.executable).resolve()

    task_xml = (
        '<?xml version="1.0" encoding="UTF-16"?>'
        '<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">'
        '<RegistrationInfo><Description>Claude Desktop Brief — auto-generate daily summary at 08:00 and 20:00</Description></RegistrationInfo>'
        '<Triggers>'
        '<CalendarTrigger>'
        '<StartBoundary>2026-03-15T08:00:00</StartBoundary>'
        '<Enabled>true</Enabled>'
        '<ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay>'
        '</CalendarTrigger>'
        '<CalendarTrigger>'
        '<StartBoundary>2026-03-15T20:00:00</StartBoundary>'
        '<Enabled>true</Enabled>'
        '<ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay>'
        '</CalendarTrigger>'
        '</Triggers>'
        '<Principals><Principal><LogonType>InteractiveToken</LogonType><RunLevel>HighestAvailable</RunLevel></Principal></Principals>'
        '<Settings>'
        '<MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>'
        '<DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>'
        '<StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>'
        '<RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>'
        '<ExecutionTimeLimit>PT1H</ExecutionTimeLimit>'
        '<Hidden>true</Hidden>'
        '</Settings>'
        '<Actions><Exec>'
        '<Command>' + str(python) + '</Command>'
        '<Arguments>"' + str(script) + '"</Arguments>'
        '</Exec></Actions>'
        '</Task>'
    )

    xml_path = Path(r"C:\Users\User\AppData\Local\Temp\claude-brief-task.xml")
    xml_path.write_text(task_xml, encoding="utf-16")

    result = subprocess.run(
        ["schtasks", "/create", "/tn", "ClaudeDesktopBrief", "/xml", str(xml_path), "/f"],
        capture_output=True, text=True
    )
    xml_path.unlink(missing_ok=True)

    log = logging.getLogger("brief")
    if result.returncode == 0:
        log.info("Task 'ClaudeDesktopBrief' registered — runs daily at 08:00 and 20:00")
    else:
        log.error("Task registration failed: %s", result.stderr.strip())


def uninstall_task() -> None:
    """Remove the ClaudeDesktopBrief scheduled task."""
    log = logging.getLogger("brief")
    result = subprocess.run(
        ["schtasks", "/delete", "/tn", "ClaudeDesktopBrief", "/f"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        log.info("Task 'ClaudeDesktopBrief' removed")
    else:
        log.error("Could not remove task: %s", result.stderr.strip())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    """Generate and write the Claude Desktop brief."""
    parser = argparse.ArgumentParser(description="Claude Desktop Brief generator")
    parser.add_argument("--dry-run",   action="store_true", help="Print to stdout, don't write")
    parser.add_argument("--install",   action="store_true", help="Install scheduled tasks (08:00 + 20:00)")
    parser.add_argument("--uninstall", action="store_true", help="Remove scheduled tasks")
    args = parser.parse_args()

    log = setup_logging()

    if args.install:
        install_task()
        return
    if args.uninstall:
        uninstall_task()
        return

    log.info("")
    log.info("=" * 60)
    log.info("CLAUDE DESKTOP BRIEF — %s%s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), " [DRY RUN]" if args.dry_run else "")
    log.info("=" * 60)

    content = generate_brief(log)
    ok = write_brief(content, log, args.dry_run)

    log.info("=" * 60)
    log.info("DONE — Status: %s", "OK" if ok else "FAILED")
    log.info("=" * 60)

    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
