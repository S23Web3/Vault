"""
Error audit: parse bot log and categorise every ERROR/WARNING line.
Run: python scripts/run_error_audit.py
"""
import re
import sys
import logging
from pathlib import Path
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

ROOT     = Path(__file__).resolve().parent.parent
LOG_FILE = ROOT / "logs" / "2026-03-03-bot.log"
OUT_FILE = ROOT / "logs" / "error_audit_2026-03-03.md"

CATEGORIES = {
    "TTP_CLOSE_FAIL":   ["109400", "reduceOnly"],
    "AUTH_FAIL":        ["100001", "Signature verification", "signature mismatch"],
    "EXIT_DETECTION":   ["EXIT_UNKNOWN", "SL_HIT_ASSUMED", "_detect_exit"],
    "RECONCILE":        ["reconcil", "Reconcile"],
    "WS_ERROR":         ["WebSocket", "ws_dead", "reconnect"],
    "API_TIMEOUT":      ["timeout", "ConnectionError", "ReadTimeout"],
}


def categorise(line: str) -> str:
    """Return category key for a log line, or OTHER."""
    for cat, keywords in CATEGORIES.items():
        for kw in keywords:
            if kw.lower() in line.lower():
                return cat
    return "OTHER"


def main() -> None:
    """Parse log file and write categorised error report."""
    if not LOG_FILE.exists():
        log.error("Log file not found: " + str(LOG_FILE))
        sys.exit(1)

    log.info("Parsing: " + str(LOG_FILE))
    buckets: dict[str, list[str]] = {cat: [] for cat in CATEGORIES}
    buckets["OTHER"] = []

    with open(LOG_FILE, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.rstrip()
            if "[ERROR]" not in line and "[WARNING]" not in line:
                continue
            cat = categorise(line)
            buckets[cat].append(line)

    log.info("Categorisation complete — writing report")
    lines = [
        "# Bot Error Audit — 2026-03-03",
        "",
        "Source: `logs/2026-03-03-bot.log`",
        "",
        "| Category | Count | First Occurrence | Last Occurrence |",
        "|----------|-------|-----------------|----------------|",
    ]

    ts_re = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})")

    for cat, entries in buckets.items():
        if not entries:
            continue
        first_ts = last_ts = ""
        for e in entries:
            m = ts_re.match(e)
            if m:
                first_ts = m.group(1)
                break
        for e in reversed(entries):
            m = ts_re.match(e)
            if m:
                last_ts = m.group(1)
                break
        lines.append("| " + cat + " | " + str(len(entries)) + " | " + first_ts + " | " + last_ts + " |")

    lines += ["", "## Sample Lines Per Category", ""]

    for cat, entries in buckets.items():
        if not entries:
            continue
        lines += ["### " + cat, ""]
        for e in entries[:5]:
            lines.append("```")
            lines.append(e[:200])
            lines.append("```")
        if len(entries) > 5:
            lines.append("_... and " + str(len(entries) - 5) + " more_")
        lines.append("")

    OUT_FILE.parent.mkdir(exist_ok=True)
    OUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    log.info("Report written: " + str(OUT_FILE))

    total = sum(len(v) for v in buckets.values())
    log.info("Total error/warning lines: %d", total)
    for cat, entries in buckets.items():
        if entries:
            log.info("  %-20s %d", cat, len(entries))


if __name__ == "__main__":
    main()
