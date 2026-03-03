# 2026-03-03 — BingX Dashboard v1-4 Patches + Handoff

## Session Summary

Continued from context-limited session on 2026-03-02. Built v1-4 dashboard via build script, applied patch1, wrote patch2. Session ended at context limit again.

---

## What Was Completed This Session

### 1. build_dashboard_v1_4.py — Audit + patch1 fix

- Audited all 15 safe_replace anchors against v1-3 source — all PASS
- Fixed markdown lints (MD022/MD031/MD032/MD040) in TOPIC-bingx-connector.md and session log
- User ran dashboard and got crash: `DuplicateCallback: allow_duplicate requires prevent_initial_call`
  - Root cause: CB-T3 used `allow_duplicate=True` with no `prevent_initial_call`
  - Fix: wrote `build_dashboard_v1_4_patch1.py` — adds `prevent_initial_call='initial_duplicate'` to CB-T3
  - py_compile: PASS

### 2. Dash Skill Updated

- Appended PART 5 to `C:\Users\User\.claude\skills\dash\SKILL.md` (v1.3)
- 9 sections covering BingX dashboard v1–v1.4 production findings:
  CSS variable root override, allow_duplicate rules, tab performance, StringIO fix,
  bot process management, bot status feed, suppress_callback_exceptions, hyphenated filename import, metrics traps

### 3. New Issues Reported (user screenshot + traceback)

User reported after running patch1:
- Activity Log too small (capped height)
- Every status message doubled (Config loaded x2, Strategy loaded x2, etc.)
- Repeating `IndexError: list index out of range` in `flat_data[ind]`

### 4. Diagnosis

**Doubled output** — `build_dashboard_v1_3_patch7.py` was applied to `main.py` TWICE.
Result: duplicate `write_bot_status` function definition (lines 165 and 191), duplicate
`BOT_ROOT`/`STATUS_PATH` constants (lines 161-162 and 187-188), duplicate clear-on-start
block (lines 213-218 and 219-224), and duplicate call sites at all 5 status write locations
(lines 250-251, 276-277, 284-285, 310-311, 346-347).

**IndexError** — CB-S1 (no `prevent_initial_call`) and CB-T3 (`prevent_initial_call='initial_duplicate'`)
both listen to `status-interval`. Dash's `_prepare_grouping` fails when dispatching these
on the same trigger at initial load. Root cause: `initial_duplicate` fires on page load AND
on subsequent ticks, but the argument indexing mismatch with CB-S1 causes the IndexError.

**Height cap** — `max-height: 180px` in `.status-feed-panel` CSS.

### 5. Additional User Reports

After patch2 was written (not yet confirmed running):
- Bot stopped but header still shows "LIVE" — fixed in P9 (add `_is_bot_running()` to CB-3)
- No Telegram message on stop — expected: `taskkill /F` force-kills without cleanup
- Start/Stop should be a single toggle button — fixed in P5/P6/P7

### 6. build_dashboard_v1_4_patch2.py Written

**File:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_dashboard_v1_4_patch2.py`
**py_compile:** PASS

13 patches across 3 files:

| Patch | File | Change |
|-------|------|--------|
| P1 | main.py | Remove duplicate write_bot_status block (entire second function definition) |
| P2 | main.py | Remove duplicate clear-on-start block |
| P3a-P3e | main.py | Remove 5 duplicate call site pairs |
| P4 | dashboard.css | max-height 180px -> 360px in .status-feed-panel |
| P5 | v1-4.py | Replace Start+Stop buttons with single `bot-toggle-btn` in layout |
| P6 | v1-4.py | Replace CB-T1+CB-T2 with `toggle_bot_cb` (writes stop event to bot-status.json) |
| P7 | v1-4.py | CB-T3: `prevent_initial_call='initial_duplicate'` -> `True` (fixes IndexError) |
| P8 | v1-4.py | CB-3: add `status-interval` as input so header refreshes every 5s |
| P9 | v1-4.py | CB-3: add OFFLINE check — header shows OFFLINE when bot not running |

---

## Current State of Key Files

| File | Version/Status |
|------|---------------|
| `bingx-live-dashboard-v1-4.py` | Built by build_dashboard_v1_4.py. patch1 applied. **patch2 status unknown** — may or may not have run |
| `main.py` | Has patch7 applied TWICE (duplicates). **patch2 may or may not have fixed this** |
| `assets/dashboard.css` | Has patch6 CSS variables. max-height still 180px if patch2 not run |
| `scripts/build_dashboard_v1_4_patch2.py` | Written this session. py_compile PASS. Not confirmed run by user |
| `scripts/build_dashboard_v1_4_patch1.py` | Written prior session. py_compile PASS. Fixes CB-T3 prevent_initial_call |

---

## Error at Session End (STILL OPEN)

```
KeyError: '..bot-run-status.children...start-bot-btn.disabled...stop-bot-btn.disabled..'
IndexError: list index out of range in flat_data[ind]
```

**Diagnosis of this specific error:**

The `KeyError: start-bot-btn.disabled` means the browser is using a STALE callback map from
before patch2 was applied. Dash sends the callback map to the browser on first load. If the
dashboard was restarted after patch2 but the browser was NOT hard-refreshed, the browser
still calls the old `start-bot-btn.disabled` callback which no longer exists.

**Fix: `Ctrl+Shift+R` (hard refresh) in the browser after restarting the dashboard.**

If patches are not applying (FAIL anchors), verify patch2 ran successfully by checking its output.

---

## What the Next Session Must Do

### Step 1 — Verify patch2 ran

Run the patch script if not already done:
```
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector"
python scripts/build_dashboard_v1_4_patch2.py
```

Check output: all 13 patches should show PASS. If any show FAIL, read the failure message
and diagnose which anchor didn't match. Read the current file to find the actual text.

### Step 2 — Restart dashboard + hard refresh

```
python bingx-live-dashboard-v1-4.py
```

Then in the browser: **Ctrl+Shift+R** (hard refresh, not just F5).

This clears the stale callback map that causes `KeyError: start-bot-btn.disabled`.

### Step 3 — Verify all fixes

- [ ] Activity Log shows more content (360px height)
- [ ] No doubled messages after restarting main.py
- [ ] Toggle button shows "Start Bot" (green) when offline, "Stop Bot" (red) when running
- [ ] Header shows "OFFLINE" when bot not running, "LIVE" when running + demo_mode=false
- [ ] No more IndexError in Flask log
- [ ] Clicking Stop Bot writes "Bot stopped by dashboard" to Activity Log

### Step 4 — If any patch2 anchor FAILed

Read the current state of the target file and diagnose. Likely cause: a previous patch or
manual edit changed the surrounding text. Write a targeted one-line fix patch.

---

## Key Files (full paths)

```
C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\
  bingx-live-dashboard-v1-4.py          -- main dashboard (current version)
  main.py                                -- bot entry point (has patch7 duplicates)
  assets\dashboard.css                   -- CSS overrides
  scripts\
    build_dashboard_v1_4.py             -- built v1-4 from v1-3 (15 patches)
    build_dashboard_v1_4_patch1.py      -- fixes CB-T3 prevent_initial_call crash
    build_dashboard_v1_4_patch2.py      -- 13 patches: dedup main.py + toggle + OFFLINE
```

## TOPIC file

`C:\Users\User\.claude\projects\c--Users-User-Documents-Obsidian-Vault\memory\TOPIC-bingx-connector.md`

---

## Technical Context for Next Session

### Bot process management (dashboard side)

```python
# In bingx-live-dashboard-v1-4.py
_is_bot_running()    # checks bot.pid file + tasklist
_start_bot_process() # subprocess.Popen + writes bot.pid
_stop_bot_process()  # taskkill /F /PID <pid> -- FORCE KILL, no cleanup
```

Force kill means: Telegram "BOT STOPPING" message in main.py NEVER fires on dashboard stop.
This is by design. The toggle callback (patch2) writes "Bot stopped by dashboard" to
bot-status.json instead.

### CB-T3 + CB-S1 on same interval (root cause of IndexError)

Both CB-S1 (load_bot_status) and CB-T3 (poll_bot_running) trigger on `status-interval`.
CB-S1 has no prevent_initial_call. CB-T3 had `initial_duplicate` (now fixed to `True`).
When `initial_duplicate` was set, Dash's _prepare_grouping received a mismatched argument
count, causing `flat_data[ind]` IndexError.

### CSS variables (Patch 6 — applied)

`assets/dashboard.css` has `:root` block overriding Dash 2.x CSS custom properties
(`--Dash-Fill-Inverse-Strong` etc.). This fixes white date pickers/dropdowns in dark theme.

### bot-status.json schema

```json
{
    "bot_start": "2026-03-03T12:38:45.000000+00:00",
    "messages": [
        {"ts": "2026-03-03T12:38:45.123456+00:00", "msg": "Config loaded: 47 coins, 5m"},
        ...
    ]
}
```

Written atomically (temp file + os.replace) by main.py during startup.
Written by toggle_bot_cb on stop ("Bot stopped by dashboard").
Read every 5s by CB-S1, rendered by CB-S2.

---

## Lessons This Session

1. **Browser cache causes KeyError after callback map changes.** When IDs are removed/renamed
   (start-bot-btn -> bot-toggle-btn), the browser needs hard refresh after dashboard restart.
   This is NOT a code bug — always tell the user to Ctrl+Shift+R when changing callback IDs.

2. **`taskkill /F` is instant death — no Python cleanup runs.** Any Telegram/logging
   notifications that should fire on shutdown must be written by the CALLER (dashboard),
   not the callee (bot process), when using force kill.

3. **Patch scripts applied twice = duplicate code.** Always check if a patch was already
   applied before running it (safe_replace guard: check if anchor exists, or check if result
   already exists).
