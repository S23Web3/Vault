"""
Dead Man's Switch — PC Guardian
Runs every 96 hours. Sends Telegram + email alert asking for confirmation.
If no reply within 96 hours, deletes BitLocker key and locks C: drive.

Run once to install: python deadman_switch.py --install
Run to test alert:   python deadman_switch.py --test
Normal operation:    Runs silently via Windows Task Scheduler

File: C:/Users/User/Documents/Obsidian Vault/scripts/deadman_switch.py
"""
import os
import sys
import json
import logging
import smtplib
import argparse
import subprocess
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ---------------------------------------------------------------------------
# Config — edit these values
# ---------------------------------------------------------------------------
TELEGRAM_TOKEN   = "8646950228:AAFJ0U5Ore2a6aVzucSX4688sWQ6iqqj_zY"
TELEGRAM_CHAT_ID = "972431177"
OWNER_CHAT_ID    = 972431177          # int — only this ID can confirm

EMAIL_TO         = "malik@shortcut23.com"
EMAIL_FROM       = "malik@shortcut23.com"
CONFIG_FILE      = Path(r"E:\guardian-config.json")  # create this manually, never commit it

BITLOCKER_KEY    = Path(r"E:\bitlocker-recovery-key.txt")
STATE_FILE       = Path(r"E:\deadman-state.json")
LOG_PATH         = Path(r"E:\deadman-switch.log")
CHECK_INTERVAL_H_DEFAULT = 96   # default hours between checks (overridable via /settimer)
REPLY_WINDOW_H_DEFAULT   = 24   # default hours to reply (overridable via /settimer)

CONFIRM_WORDS    = {"ok", "alive", "confirm", "yes"}   # accepted reply keywords
LISTEN_INTERVAL  = 5        # seconds between Telegram polls in listener mode
OFFSET_FILE      = Path(r"E:\deadman-offset.json")  # tracks last processed update ID

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(str(LOG_PATH), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger("deadman")


# ---------------------------------------------------------------------------
# State management
# ---------------------------------------------------------------------------
def load_state() -> dict:
    """Load state from JSON file. Return defaults if missing."""
    defaults = {
        "last_checkin": None,
        "alert_sent_at": None,
        "armed": False,
        "lockdown_deadline": None,
        "check_interval_h": CHECK_INTERVAL_H_DEFAULT,
        "reply_window_h": REPLY_WINDOW_H_DEFAULT,
    }
    if STATE_FILE.exists():
        try:
            saved = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            defaults.update(saved)
            return defaults
        except Exception:
            pass
    return defaults


def get_intervals() -> tuple:
    """Return (check_interval_h, reply_window_h) from current state."""
    state = load_state()
    return state["check_interval_h"], state["reply_window_h"]


def save_state(state: dict) -> None:
    """Persist state to JSON file."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------
def tg_api(method: str, payload: dict) -> dict:
    """Call Telegram Bot API. Return parsed JSON response."""
    url = "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/" + method
    data = urllib.parse.urlencode(payload).encode("utf-8")
    try:
        with urllib.request.urlopen(url, data=data, timeout=15) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as exc:
        msg = str(exc).lower()
        if "timed out" in msg or "timeout" in msg:
            log.debug("Telegram API timeout (%s) — idle", method)
        else:
            log.error("Telegram API error (%s): %s", method, exc)
        return {}


def send_telegram(message: str) -> bool:
    """Send a message to the owner chat. Return True on success."""
    resp = tg_api("sendMessage", {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    })
    ok = resp.get("ok", False)
    if ok:
        log.info("Telegram alert sent")
    else:
        log.error("Telegram send failed: %s", resp)
    return ok


def check_telegram_replies(since_timestamp: float) -> bool:
    """
    Poll getUpdates for replies from owner since given timestamp.
    Return True if a valid confirmation word was received.
    """
    resp = tg_api("getUpdates", {"timeout": 5, "limit": 50})
    if not resp.get("ok"):
        return False

    for update in resp.get("result", []):
        msg     = update.get("message", {})
        chat_id = msg.get("chat", {}).get("id")
        date    = msg.get("date", 0)
        text    = msg.get("text", "").strip().lower()

        if chat_id != OWNER_CHAT_ID:
            continue
        if date < since_timestamp:
            continue
        if any(word in text for word in CONFIRM_WORDS):
            log.info("Confirmation received via Telegram: '%s'", text)
            return True

    return False


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------
def load_email_config() -> dict | None:
    """Load SMTP config from E:/guardian-config.json. Return None if missing or invalid."""
    if not CONFIG_FILE.exists():
        log.warning("Config file not found: %s — email disabled", CONFIG_FILE)
        return None
    try:
        cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        if cfg.get("smtp_pass", "").startswith("YOUR_"):
            log.warning("Email config has placeholder password — email disabled")
            return None
        return cfg
    except Exception as exc:
        log.error("Failed to read config: %s", exc)
        return None


def send_email(subject: str, body: str) -> bool:
    """Send alert email via SMTP config from E:/guardian-config.json. Return True on success."""
    cfg = load_email_config()
    if not cfg:
        return False
    try:
        msg = MIMEMultipart()
        msg["From"]    = EMAIL_FROM
        msg["To"]      = EMAIL_TO
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(cfg["smtp_host"], cfg["smtp_port"], timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.login(cfg["smtp_user"], cfg["smtp_pass"])
            server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        log.info("Email alert sent to %s", EMAIL_TO)
        return True
    except Exception as exc:
        log.error("Email send failed: %s", exc)
        return False


# ---------------------------------------------------------------------------
# BitLocker destruction
# ---------------------------------------------------------------------------
def delete_key_and_lock() -> None:
    """Delete the BitLocker recovery key and force a reboot."""
    log.warning("DEAD MAN TRIGGERED — deleting BitLocker key and rebooting")

    send_telegram(
        "<b>DEAD MAN SWITCH TRIGGERED</b>\n"
        "No confirmation received.\n"
        "BitLocker key deleted. C: drive will be locked on reboot."
    )
    send_email(
        subject="DEAD MAN SWITCH TRIGGERED",
        body=(
            "No confirmation received within " + str(REPLY_WINDOW_H) + " hours.\n"
            "BitLocker recovery key has been deleted.\n"
            "C: drive will be locked on reboot.\n\n"
            "Timestamp: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    )

    # Delete the key
    if BITLOCKER_KEY.exists():
        try:
            BITLOCKER_KEY.unlink()
            log.warning("BitLocker key deleted: %s", BITLOCKER_KEY)
        except Exception as exc:
            log.error("Failed to delete key: %s", exc)
    else:
        log.warning("BitLocker key not found at %s — already gone", BITLOCKER_KEY)

    # Force reboot in 60 seconds
    try:
        subprocess.run(["shutdown", "/r", "/t", "60",
                        "/c", "Security lockdown initiated."], check=False)
        log.warning("Reboot scheduled in 60 seconds")
    except Exception as exc:
        log.error("Reboot command failed: %s", exc)


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------
def run_check() -> None:
    """Main check cycle: send alert or verify reply, trigger if overdue."""
    log.info("Dead man switch check started")
    state = load_state()
    now   = datetime.now()
    check_h, window_h = state["check_interval_h"], state["reply_window_h"]

    # --- Phase 1: waiting for a reply ---
    if state.get("alert_sent_at"):
        sent_at  = datetime.fromisoformat(state["alert_sent_at"])
        deadline = sent_at + timedelta(hours=window_h)

        log.info("Waiting for reply — deadline: %s", deadline.strftime("%Y-%m-%d %H:%M"))
        confirmed = check_telegram_replies(sent_at.timestamp())

        if confirmed:
            log.info("PC confirmed alive — resetting timer")
            state["last_checkin"]  = now.isoformat()
            state["alert_sent_at"] = None
            state["armed"]         = False
            save_state(state)
            send_telegram("Confirmed. Timer reset. Next check in " + str(check_h) + "h.")
            return

        if now > deadline:
            log.warning("Reply deadline passed — triggering dead man switch")
            delete_key_and_lock()
            state["armed"] = True
            save_state(state)
            return

        remaining = int((deadline - now).total_seconds() / 3600)
        log.info("Still within reply window — %dh remaining", remaining)
        return

    # --- Phase 2: check if it's time to send a new alert ---
    last = state.get("last_checkin")
    if last:
        last_dt    = datetime.fromisoformat(last)
        next_check = last_dt + timedelta(hours=check_h)
        if now < next_check:
            remaining_h = int((next_check - now).total_seconds() / 3600)
            log.info("Not yet time for check — %dh until next alert", remaining_h)
            return

    # --- Send alert ---
    deadline_str = (now + timedelta(hours=window_h)).strftime("%Y-%m-%d %H:%M")
    tg_msg = (
        "<b>PC Guardian — Alive Check</b>\n\n"
        "PC not confirmed in " + str(check_h) + " hours.\n\n"
        "Reply <b>OK</b> to confirm you are alive.\n\n"
        "Deadline: <b>" + deadline_str + "</b>\n"
        "If no reply: BitLocker key deleted, C: locked."
    )
    email_body = (
        "PC Guardian — Alive Check\n\n"
        "PC not confirmed in " + str(check_h) + " hours.\n\n"
        "Reply OK to your Telegram bot to confirm.\n\n"
        "Deadline: " + deadline_str + "\n"
        "If no reply: BitLocker key deleted, C: locked permanently."
    )

    tg_ok    = send_telegram(tg_msg)
    email_ok = send_email("PC Guardian — Alive Check Required", email_body)

    if tg_ok or email_ok:
        state["alert_sent_at"] = now.isoformat()
        save_state(state)
        log.info("Alert sent. Waiting for reply by %s", deadline_str)
    else:
        log.error("Both Telegram and email failed — no alert sent")


# ---------------------------------------------------------------------------
# Remote command listener
# ---------------------------------------------------------------------------
def load_offset() -> int:
    """Load last processed Telegram update_id. Return 0 if none."""
    if OFFSET_FILE.exists():
        try:
            return json.loads(OFFSET_FILE.read_text(encoding="utf-8")).get("offset", 0)
        except Exception:
            pass
    return 0


def save_offset(offset: int) -> None:
    """Persist last processed update_id."""
    OFFSET_FILE.write_text(json.dumps({"offset": offset}), encoding="utf-8")


def handle_command(text: str) -> None:
    """Parse and execute a command received from the owner via Telegram."""
    raw  = text.strip()
    text = raw.lower()
    log.info("Command received: %s", text)

    # Any confirm word resets the alive timer automatically
    if any(word in text for word in CONFIRM_WORDS) and not text.startswith("/"):
        state = load_state()
        state["last_checkin"]  = datetime.now().isoformat()
        state["alert_sent_at"] = None
        check_h = state["check_interval_h"]
        save_state(state)
        send_telegram("Confirmed alive. Timer reset. Next check in " + str(check_h) + "h.")
        log.info("Auto-reset via confirm word: '%s'", text)
        return

    # /status
    if text in ("/status", "status"):
        state     = load_state()
        last      = state.get("last_checkin") or "never"
        alert     = state.get("alert_sent_at") or "none"
        countdown = state.get("lockdown_deadline")
        check_h   = state["check_interval_h"]
        window_h  = state["reply_window_h"]
        msg = (
            "<b>PC Guardian — Status</b>\n"
            "Last checkin   : " + last + "\n"
            "Alert sent     : " + alert + "\n"
            "Countdown      : " + (countdown if countdown else "inactive") + "\n"
            "Check interval : " + str(check_h) + "h\n"
            "Reply window   : " + str(window_h) + "h\n"
            "BitLocker key  : " + ("EXISTS" if BITLOCKER_KEY.exists() else "DELETED")
        )
        send_telegram(msg)
        return

    # /reset
    if text in ("/reset", "reset"):
        state = load_state()
        state["last_checkin"]  = datetime.now().isoformat()
        state["alert_sent_at"] = None
        save_state(state)
        send_telegram("Timer reset. Next alert in " + str(state["check_interval_h"]) + "h.")
        log.info("Timer reset via Telegram command")
        return

    # /settimer check <hours>  or  /settimer window <hours>
    if text.startswith("/settimer ") or text.startswith("settimer "):
        parts = text.split()
        if len(parts) == 3 and parts[1] in ("check", "window") and parts[2].isdigit():
            hours = int(parts[2])
            if hours < 1:
                send_telegram("Minimum is 1 hour.")
                return
            state = load_state()
            if parts[1] == "check":
                state["check_interval_h"] = hours
                send_telegram("Check interval set to <b>" + str(hours) + "h</b>. Timer reset now.")
                log.info("Check interval changed to %dh", hours)
            else:
                state["reply_window_h"] = hours
                send_telegram("Reply window set to <b>" + str(hours) + "h</b>.")
                log.info("Reply window changed to %dh", hours)
            state["last_checkin"]  = datetime.now().isoformat()
            state["alert_sent_at"] = None
            save_state(state)
        else:
            send_telegram(
                "<b>Usage:</b>\n"
                "/settimer check 96 — set check interval (default 96h)\n"
                "/settimer check 24 — check every 24h\n"
                "/settimer check 6  — check every 6h\n"
                "/settimer check 1  — check every 1h\n"
                "/settimer window 24 — set reply window (default 24h)"
            )
        return

    # /lockdown cancel
    if text in ("/lockdown cancel", "lockdown cancel"):
        state = load_state()
        if state.get("lockdown_deadline"):
            state["lockdown_deadline"] = None
            save_state(state)
            send_telegram("Lockdown countdown cancelled.")
            log.info("Lockdown cancelled via Telegram")
        else:
            send_telegram("No active lockdown countdown to cancel.")
        return

    # /lockdown <minutes>
    if text.startswith("/lockdown ") or text.startswith("lockdown "):
        parts = text.split()
        if len(parts) == 2 and parts[1].isdigit():
            minutes = int(parts[1])
            deadline = datetime.now() + timedelta(minutes=minutes)
            state = load_state()
            state["lockdown_deadline"] = deadline.isoformat()
            save_state(state)
            send_telegram(
                "<b>LOCKDOWN COUNTDOWN STARTED</b>\n"
                "Minutes: <b>" + str(minutes) + "</b>\n"
                "Triggers at: <b>" + deadline.strftime("%Y-%m-%d %H:%M:%S") + "</b>\n\n"
                "Send <b>/lockdown cancel</b> to abort."
            )
            log.warning("Lockdown countdown started: %d minutes", minutes)
        else:
            send_telegram("Usage: /lockdown 30  (minutes)\nCancel: /lockdown cancel")
        return

    # /help
    if text in ("/help", "help", "/start"):
        state   = load_state()
        check_h = state["check_interval_h"]
        window_h = state["reply_window_h"]
        send_telegram(
            "<b>PC Guardian Commands</b>\n\n"
            "/status — show current state\n"
            "/reset — reset alive timer now\n"
            "/settimer check 96 — set check interval (current: " + str(check_h) + "h)\n"
            "/settimer window 24 — set reply window (current: " + str(window_h) + "h)\n"
            "/lockdown 30 — start 30-min countdown then lock C:\n"
            "/lockdown cancel — cancel active countdown\n"
            "/help — show this message\n\n"
            "Send <b>ok</b> / <b>alive</b> / <b>confirm</b> at any time to reset timer."
        )
        return


def check_lockdown_countdown() -> None:
    """Check if an active lockdown countdown has expired and trigger if so."""
    state = load_state()
    deadline_str = state.get("lockdown_deadline")
    if not deadline_str:
        return
    deadline = datetime.fromisoformat(deadline_str)
    now = datetime.now()
    if now >= deadline:
        log.warning("Lockdown countdown expired — triggering")
        state["lockdown_deadline"] = None
        save_state(state)
        delete_key_and_lock()
    else:
        remaining = int((deadline - now).total_seconds() / 60)
        log.info("Lockdown countdown active — %d minutes remaining", remaining)


def run_listener() -> None:
    """
    Poll Telegram for commands in a loop. Runs as a long-lived process
    via a separate scheduled task. Handles /lockdown, /status, /reset, /help.
    Only accepts messages from OWNER_CHAT_ID.
    """
    import time
    log.info("Telegram command listener started")
    send_telegram(
        "<b>PC Guardian</b> — Listener online.\n"
        "Send /help for available commands."
    )

    while True:
        try:
            offset = load_offset()
            resp = tg_api("getUpdates", {"timeout": 10, "limit": 10, "offset": offset + 1})

            if resp.get("ok"):
                updates = resp.get("result", [])
                for update in updates:
                    update_id = update.get("update_id", 0)
                    msg       = update.get("message", {})
                    chat_id   = msg.get("chat", {}).get("id")
                    text      = msg.get("text", "").strip()

                    save_offset(update_id)

                    # Ignore messages from anyone other than owner
                    if chat_id != OWNER_CHAT_ID:
                        log.warning("Ignored message from unknown chat_id: %d", chat_id)
                        continue

                    if text:
                        handle_command(text)

            # Check lockdown countdown on every poll cycle
            check_lockdown_countdown()

        except Exception as exc:
            msg = str(exc).lower()
            if "timed out" in msg or "timeout" in msg:
                log.debug("Poll idle timeout — continuing")
            else:
                log.error("Listener error: %s", exc)

        time.sleep(LISTEN_INTERVAL)


# ---------------------------------------------------------------------------
# Install as scheduled task
# ---------------------------------------------------------------------------
def make_task_xml(python: Path, script: Path, args: str, description: str,
                  interval: str, execution_limit: str) -> str:
    """Generate a scheduled task XML string."""
    return (
        '<?xml version="1.0" encoding="UTF-16"?>'
        '<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">'
        '<RegistrationInfo><Description>' + description + '</Description></RegistrationInfo>'
        '<Triggers>'
        '<TimeTrigger>'
        '<Repetition><Interval>' + interval + '</Interval><StopAtDurationEnd>false</StopAtDurationEnd></Repetition>'
        '<StartBoundary>' + datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + '</StartBoundary>'
        '<Enabled>true</Enabled>'
        '</TimeTrigger>'
        '</Triggers>'
        '<Principals><Principal><LogonType>InteractiveToken</LogonType><RunLevel>HighestAvailable</RunLevel></Principal></Principals>'
        '<Settings>'
        '<MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>'
        '<DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>'
        '<StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>'
        '<RunOnlyIfNetworkAvailable>true</RunOnlyIfNetworkAvailable>'
        '<ExecutionTimeLimit>' + execution_limit + '</ExecutionTimeLimit>'
        '</Settings>'
        '<Actions><Exec>'
        '<Command>' + str(python) + '</Command>'
        '<Arguments>"' + str(script) + '" ' + args + '</Arguments>'
        '</Exec></Actions>'
        '</Task>'
    )


def install_task() -> None:
    """Register two scheduled tasks: PCGuardian (check) and PCGuardianListener (commands)."""
    script = Path(__file__).resolve()
    python = Path(sys.executable).resolve()
    xml_path = Path(r"C:\Users\User\AppData\Local\Temp\deadman-task.xml")

    # Task 1: dead man check every 6 hours
    xml_path.write_text(
        make_task_xml(python, script, "", "PC Guardian Dead Man Switch", "PT6H", "PT1H"),
        encoding="utf-16"
    )
    r = subprocess.run(["schtasks", "/create", "/tn", "PCGuardian", "/xml", str(xml_path), "/f"],
                       capture_output=True, text=True)
    if r.returncode == 0:
        log.info("Task 'PCGuardian' registered — runs every 6 hours")
    else:
        log.error("PCGuardian task failed: %s", r.stderr.strip())

    # Task 2: Telegram listener — restarts every 30 min (acts as watchdog if it crashes)
    xml_path.write_text(
        make_task_xml(python, script, "--listen", "PC Guardian Telegram Listener", "PT30M", "PT29M"),
        encoding="utf-16"
    )
    r = subprocess.run(["schtasks", "/create", "/tn", "PCGuardianListener", "/xml", str(xml_path), "/f"],
                       capture_output=True, text=True)
    if r.returncode == 0:
        log.info("Task 'PCGuardianListener' registered — Telegram command listener")
    else:
        log.error("PCGuardianListener task failed: %s", r.stderr.strip())

    xml_path.unlink(missing_ok=True)
    log.info("Installation complete. Commands: /help /status /reset /lockdown <min>")


def uninstall_task() -> None:
    """Remove both PCGuardian scheduled tasks."""
    for tn in ["PCGuardian", "PCGuardianListener"]:
        result = subprocess.run(["schtasks", "/delete", "/tn", tn, "/f"],
                                capture_output=True, text=True)
        if result.returncode == 0:
            log.info("Task '%s' removed", tn)
        else:
            log.error("Could not remove '%s': %s", tn, result.stderr.strip())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    """Parse args and run appropriate action."""
    parser = argparse.ArgumentParser(description="PC Guardian Dead Man Switch")
    parser.add_argument("--install",   action="store_true", help="Install as scheduled tasks")
    parser.add_argument("--uninstall", action="store_true", help="Remove scheduled tasks")
    parser.add_argument("--test",      action="store_true", help="Send test alert now")
    parser.add_argument("--reset",     action="store_true", help="Reset timer (mark alive now)")
    parser.add_argument("--listen",    action="store_true", help="Run Telegram command listener")
    args = parser.parse_args()

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    if args.install:
        install_task()
    elif args.uninstall:
        uninstall_task()
    elif args.test:
        log.info("Sending test alert...")
        send_telegram(
            "<b>PC Guardian — TEST</b>\n"
            "This is a test message. Your dead man switch is working.\n"
            "Send /help to see available commands."
        )
        send_email(
            "PC Guardian — TEST",
            "This is a test message. Your dead man switch is working.\nSend /help on Telegram for commands."
        )
    elif args.reset:
        state = load_state()
        state["last_checkin"]  = datetime.now().isoformat()
        state["alert_sent_at"] = None
        save_state(state)
        log.info("Timer reset — next alert in %dh", CHECK_INTERVAL_H)
    elif args.listen:
        run_listener()
    else:
        run_check()


if __name__ == "__main__":
    main()
