r"""
Build script: creates scripts/data_scheduler.py

Autorun scheduler that runs Bybit and BingX daily updaters on a timed loop.
Calls each updater as a subprocess so crashes in one don't kill the other.

Run:  python "C:/Users/User/Documents/Obsidian Vault/PROJECTS/four-pillars-backtester/scripts/build_data_scheduler.py"
Then: python "C:/Users/User/Documents/Obsidian Vault/PROJECTS/four-pillars-backtester/scripts/data_scheduler.py"
      python "C:/Users/User/Documents/Obsidian Vault/PROJECTS/four-pillars-backtester/scripts/data_scheduler.py" --interval 12
      python "C:/Users/User/Documents/Obsidian Vault/PROJECTS/four-pillars-backtester/scripts/data_scheduler.py" --bingx-only
"""

import py_compile
from pathlib import Path

ROOT = Path(r"C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester")
OUT = ROOT / "scripts" / "data_scheduler.py"

CODE = r'''"""
Autorun scheduler for Bybit and BingX daily data updaters.

Runs both updaters on a timed loop (default: every 6 hours).
Each updater runs as a subprocess so crashes are isolated.
Designed to run in a background terminal.

Usage:
    python "C:/Users/User/Documents/Obsidian Vault/PROJECTS/four-pillars-backtester/scripts/data_scheduler.py"
    python "C:/Users/User/Documents/Obsidian Vault/PROJECTS/four-pillars-backtester/scripts/data_scheduler.py" --interval 12
    python "C:/Users/User/Documents/Obsidian Vault/PROJECTS/four-pillars-backtester/scripts/data_scheduler.py" --bingx-only
    python "C:/Users/User/Documents/Obsidian Vault/PROJECTS/four-pillars-backtester/scripts/data_scheduler.py" --bybit-only
    python "C:/Users/User/Documents/Obsidian Vault/PROJECTS/four-pillars-backtester/scripts/data_scheduler.py" --once
"""

import argparse
import datetime
import logging
import subprocess
import sys
import time
from pathlib import Path

# ── constants ─────────────────────────────────────────────────────────────

ROOT = Path(r"C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester")
SCRIPTS = ROOT / "scripts"
LOG_DIR = ROOT / "logs"

BYBIT_UPDATER = SCRIPTS / "daily_update.py"
BINGX_UPDATER = SCRIPTS / "daily_bingx_update.py"

DEFAULT_INTERVAL_HOURS = 6


def setup_logging():
    """Configure dual logging: file + console with timestamps."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.date.today().isoformat()
    log_file = LOG_DIR / f"{today}-data-scheduler.log"

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)

        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(fmt)
        logger.addHandler(ch)

    return logger


def run_updater(script_path, label):
    """Run an updater script as subprocess. Returns True on success."""
    if not script_path.exists():
        logging.warning("SKIP %s: %s not found", label, script_path)
        return False

    logging.info("--- Running %s ---", label)
    t0 = time.time()

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(ROOT),
            timeout=7200,  # 2 hour timeout per updater
            capture_output=False,
        )
        elapsed = time.time() - t0
        if result.returncode == 0:
            logging.info("%s completed in %.0f seconds", label, elapsed)
            return True
        else:
            logging.error("%s exited with code %d (%.0fs)", label, result.returncode, elapsed)
            return False
    except subprocess.TimeoutExpired:
        logging.error("%s TIMED OUT after 2 hours", label)
        return False
    except Exception as e:
        logging.error("%s FAILED: %s", label, e)
        return False


def run_cycle(run_bybit, run_bingx):
    """Run one update cycle. Returns (bybit_ok, bingx_ok)."""
    bybit_ok = True
    bingx_ok = True

    if run_bybit:
        bybit_ok = run_updater(BYBIT_UPDATER, "Bybit Daily Update")
    if run_bingx:
        bingx_ok = run_updater(BINGX_UPDATER, "BingX Daily Update")

    return bybit_ok, bingx_ok


def main():
    """Entry point for data scheduler."""
    parser = argparse.ArgumentParser(
        description="Autorun scheduler for Bybit + BingX daily data updaters"
    )
    parser.add_argument("--interval", type=float, default=DEFAULT_INTERVAL_HOURS,
                        help="Hours between update cycles (default 6)")
    parser.add_argument("--bingx-only", action="store_true",
                        help="Only run BingX updater")
    parser.add_argument("--bybit-only", action="store_true",
                        help="Only run Bybit updater")
    parser.add_argument("--once", action="store_true",
                        help="Run once and exit (no loop)")
    args = parser.parse_args()

    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("Data Scheduler started")
    logger.info("Interval: %.1f hours", args.interval)

    run_bybit = not args.bingx_only
    run_bingx = not args.bybit_only

    if run_bybit:
        logger.info("Bybit updater: %s %s", BYBIT_UPDATER,
                     "(EXISTS)" if BYBIT_UPDATER.exists() else "(NOT FOUND)")
    if run_bingx:
        logger.info("BingX updater: %s %s", BINGX_UPDATER,
                     "(EXISTS)" if BINGX_UPDATER.exists() else "(NOT FOUND)")

    cycle = 0
    interval_secs = args.interval * 3600

    try:
        while True:
            cycle += 1
            logger.info("")
            logger.info("=== CYCLE %d at %s ===",
                        cycle,
                        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            bybit_ok, bingx_ok = run_cycle(run_bybit, run_bingx)

            status_parts = []
            if run_bybit:
                status_parts.append("Bybit=" + ("OK" if bybit_ok else "FAIL"))
            if run_bingx:
                status_parts.append("BingX=" + ("OK" if bingx_ok else "FAIL"))
            logger.info("Cycle %d done: %s", cycle, ", ".join(status_parts))

            if args.once:
                logger.info("--once flag: exiting after single cycle")
                break

            next_run = datetime.datetime.now() + datetime.timedelta(seconds=interval_secs)
            logger.info("Next cycle at %s (sleeping %.1f hours)",
                        next_run.strftime("%Y-%m-%d %H:%M:%S"), args.interval)
            time.sleep(interval_secs)

    except KeyboardInterrupt:
        logger.info("")
        logger.info("Scheduler stopped by user (Ctrl+C)")

    logger.info("Data Scheduler exited after %d cycles", cycle)


if __name__ == "__main__":
    main()
'''

# ── write file ────────────────────────────────────────────────────────────
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(CODE.lstrip(), encoding="utf-8")
print(f"WROTE: {OUT}")

# ── py_compile ────────────────────────────────────────────────────────────
py_compile.compile(str(OUT), doraise=True)
print(f"py_compile PASS: {OUT}")
print()
print("Run commands:")
print(f'  python "{OUT}"                    # every 6 hours, both')
print(f'  python "{OUT}" --interval 12      # every 12 hours')
print(f'  python "{OUT}" --bingx-only       # BingX only')
print(f'  python "{OUT}" --bybit-only       # Bybit only')
print(f'  python "{OUT}" --once             # single run, no loop')
