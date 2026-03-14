"""
E: Drive USB Watcher — auto-triggers E: sync when SanDisk drive is plugged in.
Runs as a background Windows scheduled task (on logon).
Watches for WMI USB device insertion events matching the known serial number.

Install: python "C:/Users/User/Documents/Obsidian Vault/scripts/e_drive_watcher.py" --install
Remove:  python "C:/Users/User/Documents/Obsidian Vault/scripts/e_drive_watcher.py" --uninstall
Test:    python "C:/Users/User/Documents/Obsidian Vault/scripts/e_drive_watcher.py" --watch
"""
import sys
import time
import logging
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
# SanDisk serial — identifies the E: drive uniquely
TARGET_SERIAL   = "00005403090825034841"
TARGET_MODEL    = "SanDisk"

MILESTONE_SCRIPT = Path(r"C:\Users\User\Documents\Obsidian Vault\scripts\milestone_push.py")
LOG_PATH         = Path(r"C:\Users\User\Documents\Obsidian Vault\logs\e-drive-watcher.log")
POLL_INTERVAL    = 10   # seconds between checks when WMI watch not available

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
def setup_logging() -> logging.Logger:
    """Set up dual-handler logger."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    fmt     = "%(asctime)s [%(levelname)s] %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    logger  = logging.getLogger("watcher")
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
# Drive detection
# ---------------------------------------------------------------------------
def get_connected_drives(log: logging.Logger) -> list:
    """Return list of dicts with SerialNumber and Model for all connected disks."""
    try:
        import wmi
        c = wmi.WMI()
        drives = []
        for disk in c.Win32_DiskDrive():
            drives.append({
                "serial": (disk.SerialNumber or "").strip(),
                "model":  (disk.Model or "").strip(),
            })
        return drives
    except Exception as exc:
        log.debug("WMI drive query failed: %s", exc)
        return []


def is_target_drive_connected(log: logging.Logger) -> bool:
    """Return True if the SanDisk E: drive is currently connected."""
    drives = get_connected_drives(log)
    for d in drives:
        if TARGET_SERIAL in d["serial"] or TARGET_MODEL in d["model"]:
            return True
    # Fallback: just check if E: is mounted
    return Path(r"E:\\").exists()


# ---------------------------------------------------------------------------
# Sync trigger
# ---------------------------------------------------------------------------
def trigger_sync(log: logging.Logger) -> None:
    """Run milestone_push.py --e-only when drive is detected."""
    log.info("E: drive detected — triggering sync")
    try:
        result = subprocess.run(
            [sys.executable, str(MILESTONE_SCRIPT), "--e-only"],
            capture_output=True, text=True, timeout=7200
        )
        if result.returncode == 0:
            log.info("E: sync completed successfully")
        else:
            log.error("E: sync failed (exit %d): %s", result.returncode, result.stderr.strip())
        if result.stdout.strip():
            for line in result.stdout.strip().splitlines():
                log.info("  %s", line)
    except subprocess.TimeoutExpired:
        log.error("E: sync timed out after 2 hours")
    except Exception as exc:
        log.error("Failed to trigger sync: %s", exc)


# ---------------------------------------------------------------------------
# WMI event watcher (preferred — instant detection)
# ---------------------------------------------------------------------------
def watch_wmi(log: logging.Logger) -> None:
    """
    Use WMI event subscription to detect USB insertion instantly.
    Falls back to polling if WMI is unavailable.
    """
    try:
        import wmi
        c = wmi.WMI()
        watcher = c.Win32_DeviceChangeEvent.watch_for("creation")
        log.info("WMI event watcher active — waiting for E: drive insertion")

        drive_was_present = is_target_drive_connected(log)
        if drive_was_present:
            log.info("E: drive already connected at startup — syncing now")
            trigger_sync(log)

        while True:
            try:
                watcher(timeout_ms=5000)
                # Event fired — check if it's our drive
                time.sleep(3)  # brief wait for drive to mount fully
                if is_target_drive_connected(log) and not drive_was_present:
                    trigger_sync(log)
                    drive_was_present = True
                elif not is_target_drive_connected(log):
                    if drive_was_present:
                        log.info("E: drive removed")
                    drive_was_present = False
            except wmi.x_wmi_timed_out:
                # Normal — no event in 5s window, keep watching
                current = is_target_drive_connected(log)
                if current and not drive_was_present:
                    log.info("E: drive detected (poll fallback)")
                    trigger_sync(log)
                elif not current and drive_was_present:
                    log.info("E: drive removed")
                drive_was_present = current

    except ImportError:
        log.warning("WMI module not available — falling back to polling every %ds", POLL_INTERVAL)
        watch_poll(log)
    except Exception as exc:
        log.error("WMI watcher error: %s — falling back to polling", exc)
        watch_poll(log)


# ---------------------------------------------------------------------------
# Polling fallback
# ---------------------------------------------------------------------------
def watch_poll(log: logging.Logger) -> None:
    """Poll every POLL_INTERVAL seconds for E: drive insertion."""
    log.info("Polling for E: drive every %ds", POLL_INTERVAL)
    was_present = is_target_drive_connected(log)

    if was_present:
        log.info("E: drive already connected at startup — syncing now")
        trigger_sync(log)

    while True:
        time.sleep(POLL_INTERVAL)
        now_present = is_target_drive_connected(log)
        if now_present and not was_present:
            log.info("E: drive plugged in — triggering sync")
            trigger_sync(log)
        elif not now_present and was_present:
            log.info("E: drive removed")
        was_present = now_present


# ---------------------------------------------------------------------------
# Install / uninstall scheduled task
# ---------------------------------------------------------------------------
def install_task(log: logging.Logger) -> None:
    """Register EDriveWatcher as a scheduled task that runs on user logon."""
    script = Path(__file__).resolve()
    python = Path(sys.executable).resolve()

    task_xml = (
        '<?xml version="1.0" encoding="UTF-16"?>'
        '<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">'
        '<RegistrationInfo><Description>E: Drive USB watcher — auto-sync on plug-in</Description></RegistrationInfo>'
        '<Triggers>'
        '<LogonTrigger><Enabled>true</Enabled><Delay>PT30S</Delay></LogonTrigger>'
        '</Triggers>'
        '<Principals><Principal><LogonType>InteractiveToken</LogonType><RunLevel>HighestAvailable</RunLevel></Principal></Principals>'
        '<Settings>'
        '<MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>'
        '<DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>'
        '<StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>'
        '<ExecutionTimeLimit>PT0S</ExecutionTimeLimit>'
        '<Hidden>true</Hidden>'
        '</Settings>'
        '<Actions><Exec>'
        '<Command>' + str(python) + '</Command>'
        '<Arguments>"' + str(script) + '" --watch</Arguments>'
        '</Exec></Actions>'
        '</Task>'
    )

    xml_path = Path(r"C:\Users\User\AppData\Local\Temp\watcher-task.xml")
    xml_path.write_text(task_xml, encoding="utf-16")

    result = subprocess.run(
        ["schtasks", "/create", "/tn", "EDriveWatcher", "/xml", str(xml_path), "/f"],
        capture_output=True, text=True
    )
    xml_path.unlink(missing_ok=True)

    if result.returncode == 0:
        log.info("Task 'EDriveWatcher' registered — starts on logon, watches for SanDisk E: drive")
        log.info("Plug in the drive at the office — sync triggers automatically within 10 seconds")
    else:
        log.error("Task registration failed: %s", result.stderr.strip())


def uninstall_task(log: logging.Logger) -> None:
    """Remove the EDriveWatcher scheduled task."""
    result = subprocess.run(
        ["schtasks", "/delete", "/tn", "EDriveWatcher", "/f"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        log.info("Task 'EDriveWatcher' removed")
    else:
        log.error("Could not remove task: %s", result.stderr.strip())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    """Parse args and run."""
    parser = argparse.ArgumentParser(description="E: Drive USB watcher")
    parser.add_argument("--watch",     action="store_true", help="Start watching (run by task scheduler)")
    parser.add_argument("--install",   action="store_true", help="Install as logon scheduled task")
    parser.add_argument("--uninstall", action="store_true", help="Remove scheduled task")
    args = parser.parse_args()

    log = setup_logging()

    if args.install:
        install_task(log)
    elif args.uninstall:
        uninstall_task(log)
    elif args.watch:
        log.info("E: Drive Watcher started — target serial: %s", TARGET_SERIAL)
        watch_wmi(log)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
