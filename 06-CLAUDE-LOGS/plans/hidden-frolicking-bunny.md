# BingX Connector — Fix M2 + UTC+4 Logging, Then Restart

## Context

Bot is STOPPED. All code fixes from previous sessions are applied and verified (67/67 tests, E1/A1/M1/SB1/SB2 all fixed). One signal DID fire (GUN-USDT LONG B, Run 1 at 14:02:20) but order failed due to E1 (json.dumps spaces) — E1 is now fixed in code.

User stays on 1m timeframe ("it is about the process, not the result").

Two outstanding fixes the user requested:
1. **M2 — bot.log relative path** — log goes to cwd, not project dir. Proven problem: found bot.log in TWO wrong locations (`C:\Users\User\bot.log` and project dir stale copy). Run 2 log is UNFINDABLE.
2. **UTC+4 logging** — user wants local time (UTC+4) in bot logs, not system default.

---

## Fix 1 — M2: bot.log absolute path + logs/ directory

**File:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main.py` lines 32-42

**Current code (line 39):**
```python
logging.FileHandler("bot.log", encoding="utf-8"),
```

**Change to:**
```python
def setup_logging():
    """Configure dual logging: file + console with UTC+4 timestamps."""
    log_dir = Path(__file__).resolve().parent / "logs"
    log_dir.mkdir(exist_ok=True)
    today = date.today().strftime("%Y-%m-%d")
    log_file = log_dir / f"{today}-bot.log"

    utc4 = timezone(timedelta(hours=4))

    class UTC4Formatter(logging.Formatter):
        """Formatter that outputs timestamps in UTC+4."""
        converter = None
        def formatTime(self, record, datefmt=None):
            """Format log record timestamp as UTC+4."""
            dt = datetime.fromtimestamp(record.created, tz=utc4)
            if datefmt:
                return dt.strftime(datefmt)
            return dt.strftime("%Y-%m-%d %H:%M:%S")

    fmt = UTC4Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
    file_handler.setFormatter(fmt)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(fmt)

    logging.basicConfig(level=logging.DEBUG, handlers=[file_handler, console_handler])
```

**What this does:**
- Log file goes to `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\logs\2026-02-25-bot.log` (always project dir, dated)
- `logs/` directory created at startup if missing
- All timestamps formatted in UTC+4
- Follows MEMORY.md LOGGING STANDARD: dated file, `logs/` dir, dual handler
- No more mystery log locations
- Uses extended import from Fix 2 (`date`, `timedelta` added to existing line 14)

---

## Fix 2 — extend datetime import

**File:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main.py` line 14

**Current:**
```python
from datetime import datetime, timezone
```

**Change to:**
```python
from datetime import datetime, timezone, timedelta, date
```

Then in the logging setup, use `timezone(timedelta(hours=4))` and `date.today()`. Line 118 (`datetime.now(timezone.utc)`) stays unchanged — no breakage.

---

## Verification

After applying both fixes:

1. Stop any running bot instance
2. Run from ANY directory:
   ```
   python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main.py"
   ```
3. Confirm log file created at:
   ```
   C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\logs\2026-02-25-bot.log
   ```
4. Confirm timestamps show UTC+4 (not UTC)
5. Confirm startup checks pass (leverage, margin, warmup, Telegram)
6. Let it run on 1m — wait for next signal to confirm E1 fix end-to-end

---

## Step 1 Checklist (updated)

- [x] All code fixes (E1, A1, M1, SB1, SB2, SB3, test fixes)
- [x] 67/67 tests passing
- [x] Telegram working
- [x] Signal pipeline proven (GUN-USDT LONG B fired in Run 1)
- [ ] **M2 fix — bot.log absolute path + logs/ dir** (this plan)
- [ ] **UTC+4 logging** (this plan)
- [ ] **Bot running continuously** — restart after fixes
- [ ] **First trade completes** — waiting for signal with E1 fix active
- [ ] **Telegram entry alert received** — waiting
- [ ] **Demo position visible in BingX VST** — waiting
