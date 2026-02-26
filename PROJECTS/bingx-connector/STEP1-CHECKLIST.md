# Step 1 Checklist — Demo Live
**Derived from:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\COUNTDOWN-TO-LIVE.md`
**Fault ref:** `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-24-fault-report-step1-build-review.md`

---

## Fixes

- [x] **Fix 3 — config.yaml** — switched plugin to `four_pillars_v384`, added `four_pillars` block (done 2026-02-24 by user)

- [x] **Fix 1 — test_executor.py line 178** — changed `assertEqual` to `assertAlmostEqual(rd(99.99, 0.01), 99.99, places=8)` (done 2026-02-25)
  - File: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\tests\test_executor.py`

- [x] **Investigate Fault 3 — plugin import** — CLEARED 2026-02-24. `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\four_pillars.py` confirmed produces `long_a`, `long_b`, `long_c`, `short_a`, `short_b`, `short_c` at lines 64-73. Import is correct. Note: uses state machine architecture vs monolithic v383_v2 — may produce different signal timing. Flag for Step 2 strategy comparison.

- [x] **Fix 2 — test_integration.py** — surfaced and fixed two bugs (done 2026-02-25):
  - Added `assertIsNotNone` after `execute()` to surface silent failure
  - Root cause: `@patch("executor.requests.get")` and `@patch("position_monitor.requests.get")` both patch the same shared `requests` module — outer patch won, had no side_effect. Fixed by patching `requests.get` once with 3 sequential responses (price, step size, positions).
  - File: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\tests\test_integration.py`

- [x] **Fix 3 — state_manager.py shallow copy bug** — `dict(DEFAULT_STATE)` was a shallow copy; `open_positions` dict was shared across instances, causing test pollution. Fixed with `copy.deepcopy(DEFAULT_STATE)`. Production bug also fixed. (done 2026-02-25)
  - File: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\state_manager.py`

---

## Verification

- [x] **Run all tests — 67/67 PASSED** (2026-02-25)
  ```
  python -m pytest "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\tests\" -v
  ```

- [x] **M2 fix — bot.log absolute path** — log now writes to `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\logs\YYYY-MM-DD-bot.log` (done 2026-02-25 session 5)
- [x] **UTC+4 logging** — all timestamps in UTC+4 via custom formatter in `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main.py` (done 2026-02-25 session 5)
- [x] **UTC+4 Telegram** — Telegram notifications now show UTC+4 in `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\notifier.py` (done 2026-02-25 session 5)
- [x] **Signal pipeline proven** — GUN-USDT LONG B fired at 14:02:20 (Run 1). Order failed due to E1 (now fixed in code).

- [ ] **Add 37 more coins** — expand `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\config.yaml` from 3 to 40 coins, update `max_positions` in risk config
- [ ] **Restart bot in demo mode**
  ```
  python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main.py"
  ```
  - Log file at: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\logs\YYYY-MM-DD-bot.log`
  - Bot logs startup, connects BingX VST
  - Timestamps in UTC+4, Telegram in UTC+4
  - No crash after 5 minutes running

- [ ] **First demo trade completes** — A or B grade signal fires, order placed on BingX VST
- [ ] **Telegram entry alert received** — with UTC+4 timestamp
- [ ] **Position visible in BingX VST account** — demo order placed and open

---

## Step 1 complete when all boxes are checked
