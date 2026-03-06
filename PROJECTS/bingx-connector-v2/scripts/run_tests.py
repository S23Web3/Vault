"""
Run pytest suite and save output to logs/YYYY-MM-DD-tests.log.
Run: python scripts/run_tests.py
"""
import sys
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = ROOT / "logs"


def main():
    """Run pytest, mirror output to console and dated log file."""
    LOGS_DIR.mkdir(exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log_path = LOGS_DIR / (today + "-tests.log")
    run_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    header = (
        "\n"
        + "=" * 72 + "\n"
        + "TEST RUN: " + run_ts + "\n"
        + "=" * 72 + "\n"
    )
    print(header, end="")
    with open(log_path, "a", encoding="utf-8") as log_f:
        log_f.write(header)
        proc = subprocess.Popen(
            [sys.executable, "-m", "pytest", "tests/", "-v",
             "--tb=short"],
            cwd=str(ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
        )
        for line in proc.stdout:
            print(line, end="")
            log_f.write(line)
        proc.wait()
    footer = (
        "\nEXIT CODE: " + str(proc.returncode) + "\n"
        + "LOG: " + str(log_path) + "\n"
    )
    print(footer, end="")
    with open(log_path, "a", encoding="utf-8") as log_f:
        log_f.write(footer)
    sys.exit(proc.returncode)


if __name__ == "__main__":
    main()
