# BingX Dashboard v1.5 — Runtime Error Fix Plan

Date: 2026-03-05

## Context

Dashboard v1.5 was built 2026-03-04 (Phase 3 of the v1.5 full audit/upgrade). It passed `py_compile` but was never run until today. First launch revealed two code errors and one API error. The v2 continuation prompt (`C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-05-next-chat-prompt-v2.md`) listed only the `be_act` settings save bug — these runtime errors are new findings.

## Errors Found

| # | Error | Line | Root Cause |
|---|-------|------|-----------|
| 1 | `KeyError: "Callback function not found for output 'store-bot-status.data'."` | 1141 | `dcc.Store(id='store-bot-status', data=[])` — only store not using `storage_type='memory'`. The `data=[]` initial value may confuse Dash's callback registration when combined with a callback that writes to the same property. All 4 other stores use `storage_type='memory'` and work fine. |
| 2 | `IndexError: list index out of range` in `_prepare_grouping` | Dash internal | Likely cascading from Error 1. Dash's internal `flat_data` array gets misaligned when a store callback fails to register. Will re-test after fixing Error 1. |
| 3 | `BingX error 100001: Signature verification failed` | API auth | Separate from code bugs. P3-A patch added `recvWindow='10000'` to `_sign()` but credentials may be expired/wrong. Not a code fix — user needs to verify `.env` keys. |

## Fix: Build Script

**Build script**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_dashboard_v1_5_patch_runtime.py`
**Base file**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx-live-dashboard-v1-5.py`
**Output**: Patches the base file in-place (single line change)

### Patch 1: Fix store-bot-status definition (line 1141)

```
OLD: dcc.Store(id='store-bot-status', data=[]),
NEW: dcc.Store(id='store-bot-status', storage_type='memory'),
```

This aligns `store-bot-status` with all other stores (lines 1137-1140) and removes the ambiguous initial `data=[]` that conflicts with CB-S1's callback output.

### Patch 2 (if IndexError persists after Patch 1): Investigate further

The IndexError at `_prepare_grouping` fires at t+14s (around the 3rd status-interval tick). If it persists after Patch 1, the next candidate is a callback with mismatched browser-sent data. Callbacks to inspect:
- CB-3 (line 1252): 4 inputs including `store-unrealized` which has no initial data
- CB-9 (line 1933): 5 inputs + 1 state, `prevent_initial_call=True` — should be safe
- CB-10 (line 2089): references `coin-period-filter` — verify it exists in layout

## Scope

**IN scope:**
- Fix 1: store-bot-status definition (line 1141)
- py_compile validation
- Retest (user runs dashboard, verifies no more KeyError/IndexError)

**OUT of scope (separate tasks from v2 prompt):**
- `be_act` settings save bug (Task 2 in v2 prompt)
- dashboard_v395 backtester preset (Task 1 in v2 prompt)
- API credential fix (user action — verify `.env` keys)

## Critical Files

- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx-live-dashboard-v1-5.py` (line 1141)
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_dashboard_v1_5_patch_runtime.py` (new build script)

## Verification

1. Build script writes the patch and runs `py_compile` on the result
2. User runs: `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx-live-dashboard-v1-5.py"`
3. Check console: no `KeyError: store-bot-status.data` on page load
4. Check console: no `IndexError: list index out of range` in first 30 seconds
5. Signature errors (100001) will persist until `.env` keys are updated — that's expected and separate
