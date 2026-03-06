# Plan: Fix BingX 109400 "timestamp is invalid" Error

## Context

The bot and dashboard use raw `time.time() * 1000` for API request timestamps. BingX rejects requests where the timestamp drifts >5 seconds from their server clock (error 109400). There is **zero server time synchronization** in the codebase. This caused the user to lose 17% — when timestamps go invalid, position reconciliation, SL moves, TTP closes, and balance queries all fail silently (logged as warnings, fall back to local state).

**API doc confirmation** (`BINGX-API-V3-COMPLETE-REFERENCE.md` lines 323, 433-453):
- Timestamp must be within 5000ms of server time
- Public endpoint: `GET /openApi/swap/v2/server/time` → `{"data": {"serverTime": ms}}`

## Root Cause

Two independent timestamp generation points, both unsynchronized:

1. **Bot**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx_auth.py` line 43 — `params["timestamp"] = str(int(time.time() * 1000))`
2. **Dashboard**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx-live-dashboard-v1-4.py` line 193 — `params['timestamp'] = int(time.time() * 1000)`

## Fix — Server Time Sync Module

### New file: `time_sync.py`

Create `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\time_sync.py`:
- `TimeSync` class — fetches server time, calculates offset (server_time - local_time), thread-safe
- `sync()` — single fetch with RTT midpoint compensation
- `now_ms()` — returns `int(time.time() * 1000) + offset`
- `start_periodic()` — daemon Timer thread, re-syncs every 30s
- `force_resync()` — immediate sync (called on 109400 error)
- `get_time_sync(base_url)` — module-level singleton factory
- `synced_timestamp_ms()` — convenience function, falls back to raw time if never synced
- Supports both live (`open-api.bingx.com`) and demo (`open-api-vst.bingx.com`) base URLs

### Modify: `bingx_auth.py` (3-line change)

- Add `from time_sync import synced_timestamp_ms`
- Replace line 43: `str(int(time.time() * 1000))` → `str(synced_timestamp_ms())`
- Remove unused `import time`

All bot API calls (main.py, executor.py, position_monitor.py, ws_listener.py) flow through `build_signed_request()` — automatically fixed.

### Modify: `main.py` (startup init)

- Import `get_time_sync`
- After `auth = BingXAuth(...)`: create singleton, call `sync()`, call `start_periodic()`
- Before shutdown: call `stop_periodic()`

### Modify: `bingx-live-dashboard-v1-4.py` (3 changes)

- Import `synced_timestamp_ms, get_time_sync`
- At startup: init singleton, sync, start periodic
- Line 193: replace `int(time.time() * 1000)` → `synced_timestamp_ms()`

### Add 109400 retry logic (3 files)

On 109400 error → `force_resync()` → rebuild request → retry once:

- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\position_monitor.py` — in `_fetch_positions()` (GET, idempotent, safe to retry)
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\executor.py` — in `execute()` order placement (retry once with fresh timestamp)
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx-live-dashboard-v1-4.py` — in `_bingx_request()` wrapper

### Files unchanged (no modifications needed)

- `ws_listener.py` — calls `auth.build_signed_request()`, gets synced time automatically
- `signal_engine.py`, `state_manager.py`, `risk_gate.py`, `data_fetcher.py` — no signed API calls

## Build Script

`C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_time_sync.py`

1. Create `time_sync.py` (check not exists first)
2. Backup `bingx_auth.py` → `.bak`
3. Write updated `bingx_auth.py`
4. Backup `main.py` → `.bak`
5. Write updated `main.py`
6. Backup `bingx-live-dashboard-v1-4.py` → `.bak`
7. Write updated dashboard
8. Backup `executor.py` → `.bak`
9. Write updated `executor.py` with 109400 retry
10. Backup `position_monitor.py` → `.bak`
11. Write updated `position_monitor.py` with 109400 retry
12. `py_compile` every written file
13. Print summary

**Run command:**
```
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector"
python scripts\build_time_sync.py
```

## Verification

After running the build script:
1. Restart the bot (`python main.py`) — check log for `TimeSync: offset=+Xms` on startup
2. Restart dashboard (`python bingx-live-dashboard-v1-4.py`) — check log for TimeSync init
3. Watch for 30s periodic sync messages in logs
4. The 109400 errors should stop. If Windows clock drifts, the offset auto-corrects every 30s
5. If a 109400 still occurs (edge case), logs will show `forced re-sync triggered` + retry

## Failure Mode

If BingX server-time endpoint is unreachable, `_offset_ms` stays 0 = raw `time.time()` = identical to current behavior. No regression.
