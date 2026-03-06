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

---

## Session Continuation — 2026-03-03 (afternoon)

### Changes Made

#### 1. Removed conflicting BingX native trailing order
- `config.yaml`: `trailing_activation_atr_mult: null`, `trailing_rate: null`
- Was placing `TRAILING_STOP_MARKET` at 2% callback rate on exchange, conflicting with TTP engine
- executor.py guard `if self.trailing_rate and self.trailing_activation_atr_mult` already handles null — no code change needed
- TTP engine (0.5% act / 0.2% trail) is now sole trailing exit mechanism

#### 2. BE raise switched to live mark price trigger
- `position_monitor.py`: `check_breakeven()` rewritten
- Old: waited for `ttp_state == "ACTIVATED"` (5m candle close → up to 105s lag)
- New: fetches live mark price per open position, triggers when `mark >= entry * (1 + ttp_act)` (LONG) or `mark <= entry * (1 - ttp_act)` (SHORT)
- No API calls made when no positions are open
- `be_raised` guard unchanged — fires exactly once per position
- py_compile: PASS

#### 3. Monitor loop poll reduced
- `config.yaml`: `position_check_sec: 60 → 30`
- BE raise now responds within ~30s of price crossing activation level
- max_positions raised to 15, max_daily_trades to 200 (user set via dashboard)

### Active Config Summary (post-session)

| Parameter | Value |
|-----------|-------|
| poll_interval_sec | 45 |
| position_check_sec | 30 |
| max_positions | 15 |
| max_daily_trades | 200 |
| trailing_activation_atr_mult | null |
| trailing_rate | null |
| ttp_enabled | true |
| ttp_act | 0.005 (0.5%) |
| ttp_dist | 0.002 (0.2%) |
| be_auto | true |

### SL Ladder (confirmed from code)

| Step | Trigger | SL location | Mechanism |
|------|---------|-------------|-----------|
| 1 | Entry | entry ± 2×ATR | STOP_MARKET on exchange |
| 2 | Live mark crosses ±0.5% | entry + commission (BE) | check_breakeven() every 30s |
| 3 | TTP trail reversal | 0.2% behind extreme | Python engine → market close |

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

---

## Session Continuation — 2026-03-03 (evening)

### Patch4 Applied — Close Market Button

**Script**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_dashboard_v1_4_patch4.py`
**Result**: 2/2 PASS, py_compile PASS, BUILD OK
**Dashboard restarted**: yes, running on http://127.0.0.1:8051

**What patch4 adds:**

| Patch | Change |
|-------|--------|
| P1 | Red "Close Market" button added after "Move SL" in Live Trades position action panel |
| P2 | CB-16 callback: cancels ALL open orders for selected symbol, places MARKET reduceOnly close, writes `close_pending=True` + `close_source="dashboard"` to state.json |

CB-16 uses `prevent_initial_call=True` and `allow_duplicate=True` on `pos-action-status` output.

**Awaiting test**: Need an open position to verify the full close flow (cancel orders + market close + state write).

### Cumulative Dashboard v1-4 Patch Status

| Patch Script | Status | Changes |
|-------------|--------|---------|
| build_dashboard_v1_4.py | APPLIED | 15 patches: v1-3 -> v1-4 (Bot Terminal tab, tab rename, status feed) |
| build_dashboard_v1_4_patch1.py | APPLIED | CB-T3 prevent_initial_call fix |
| build_dashboard_v1_4_patch2.py | APPLIED | 13 patches: dedup main.py, toggle button, OFFLINE header, 360px log |
| build_dashboard_v1_4_patch3.py | APPLIED | TTP columns + Controls toggle in dashboard |
| build_dashboard_v1_4_patch4.py | APPLIED | Close Market button + CB-16 callback |

### Current Config (live, from config.yaml)

| Parameter | Value |
|-----------|-------|
| demo_mode | false |
| margin_usd | 5.0 |
| leverage | 10 |
| coins | 47 |
| max_positions | 15 |
| max_daily_trades | 200 |
| daily_loss_limit_usd | 15.0 |
| ttp_enabled | true |
| ttp_act | 0.005 (0.5%) |
| ttp_dist | 0.002 (0.2%) |
| be_auto | true |
| tp_atr_mult | null (TTP handles exits) |
| trailing_activation_atr_mult | null (disabled — TTP is sole trailing mechanism) |
| require_stage2 | true |

### Dashboard v1-4 Feature Summary (all patches applied)

**6 tabs**: Live Trades > Bot Terminal > Strategy Parameters > History > Analytics > Coin Summary

**Live Trades tab actions** (per selected position row):
- Raise BE — cancel SL, place STOP_MARKET at entry+fees
- Move SL — place new STOP_MARKET at user-entered price
- Close Market — cancel ALL open orders, place MARKET reduceOnly close

**Bot Terminal tab**:
- Toggle button (Start/Stop) with PID tracking
- Activity Log feed (bot-status.json, 5s poll, 360px height)

**Header**: Shows LIVE/DEMO/OFFLINE status, refreshes every 5s

---

## Patch5 Written — TTP Controls + BE Buffer (not yet run)

**Script**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_dashboard_v1_4_patch5.py`
**py_compile**: PASS (build script itself)
**Status**: NOT YET RUN — awaiting user execution

### What patch5 does (5 patches across 3 files)

| Patch | File | Change |
| ----- | ---- | ------ |
| P1 | dashboard v1-4 | TTP controls row in CB-5 action panel: Act% input, Trail% input, "Set TTP" button, "Activate Now" button |
| P1b | dashboard v1-4 | TTP display variables — reads per-position overrides from state.json |
| P2 | dashboard v1-4 | CB-17 (Set TTP) writes ttp_act_override + ttp_dist_override + ttp_engine_dirty to state.json; CB-18 (Activate Now) writes ttp_force_activate=True |
| P4 | signal_engine.py | Per-position TTP overrides when creating TTPExit + force activate handling + engine dirty flag recreates engine |
| P5 | position_monitor.py | BE slippage buffer: adds 0.1% (be\_buffer=0.001) on top of commission rate in \_place\_be\_sl() |

### BE price formula after patch5

```python
LONG:  be_price = entry * (1 + commission_rate + 0.001)
SHORT: be_price = entry * (1 - commission_rate - 0.001)
```

Commission rate = 0.0016 (0.16% RT from API). Total BE offset = 0.26% above entry (LONG).

### Run command

```bash
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector"
python scripts/build_dashboard_v1_4_patch5.py
```

Then restart bot (`python main.py`) and dashboard (`python bingx-live-dashboard-v1-4.py`), hard refresh browser (`Ctrl+Shift+R`).

### Cumulative Patch Status

| Patch Script | Status | Changes |
| ------------ | ------ | ------- |
| build_dashboard_v1_4.py | APPLIED | 15 patches: v1-3 -> v1-4 |
| build_dashboard_v1_4_patch1.py | APPLIED | CB-T3 prevent_initial_call fix |
| build_dashboard_v1_4_patch2.py | APPLIED | 13 patches: dedup main.py, toggle, OFFLINE, 360px |
| build_dashboard_v1_4_patch3.py | APPLIED | TTP columns + Controls toggle |
| build_dashboard_v1_4_patch4.py | APPLIED | Close Market button + CB-16 |
| build_dashboard_v1_4_patch5.py | WRITTEN, NOT RUN | TTP per-position controls + BE buffer |

---

## Session Continuation — 2026-03-04 (late night)

### Context

Continuation from 2026-03-03 evening session. Patch5 written but not yet run. All docs updated. This short session covered verification and one optimization.

### 1. Exit Mechanics Verification (all confirmed from source code)

Full audit of all exit mechanics via Explore agent reading live source files:

| Mechanic | Status | Code Location |
| -------- | ------ | ------------- |
| Initial SL | 2.0x ATR, STOP_MARKET attached to entry | executor.py L195-200 |
| BE Raise | entry * (1 + commission_rate + 0.001) — commission + 0.1% buffer | position_monitor.py L403-408 |
| BE Trigger | Live mark price crosses entry * (1 +/- ttp_act), checks every 30s | position_monitor.py L442-486 |
| TTP Engine | Enabled, act=0.5%, dist=0.2%, per-position overrides from state.json | signal_engine.py L111-119 |
| Commission | Fetched from BingX API x2 (round-trip), fallback 0.001 | main.py L114-127 |
| BingX native trailing | Disabled (both null in config) | config.yaml L78-79 |

**Patch5 confirmed already applied** — `be_buffer = 0.001` present in position_monitor.py.

### 2. Monitor Loop Optimization

User requested: only poll exchange API when positions are actually open (bot-only account, no manual trades).

**Change**: Added early return in `position_monitor.py` `check()` method (line 252-254):

```python
state_positions = self.state.get_open_positions()
if not state_positions:
    return
```

This skips `_fetch_positions()` API call when no positions exist in state. WS fill queue is still drained before the guard (in case a fill event arrives for a just-opened position).

**py_compile**: PASS

**Effect**: Zero API calls from monitor loop when no trades are open. Previously called `_fetch_positions()` every 30s regardless.

### SL Ladder (verified from code, all 3 steps confirmed)

| Step | Trigger | SL Location | Mechanism |
| ---- | ------- | ----------- | --------- |
| 1 | Entry | entry +/- 2x ATR | STOP_MARKET on exchange |
| 2 | Mark crosses +/- 0.5% | entry + commission + 0.1% buffer | BE raise every 30s |
| 3 | TTP trail reversal | 0.2% behind extreme | Python engine -> market close |
