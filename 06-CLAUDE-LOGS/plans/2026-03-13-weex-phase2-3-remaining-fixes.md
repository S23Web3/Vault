# WEEX Phase 2/3 Opus Audit — Remaining Fixes

**Date**: 2026-03-13
**Plan file**: parallel-dazzling-marshmallow.md

---

## Context

Continuing WEEX Connector Phase 2/3 + Function Contracts Opus Audit. Prior session applied 4 critical fixes:
- `_send_heartbeat` renamed to `_handle_server_ping`
- `_on_message` docstring updated
- `atr_at_entry` added to `StateManager.add_position()`
- All 4 stochastic constants present (9-3, 14-3, 40-3, 60-10)
- Signal NamedTuple includes `atr` field

This session completes the remaining documentation fixes and session logging.

---

## Pre-flight: What's Already Done (verified by Explore agent)

- SKILL.md Phase Status: already shows Phase 2 = ARTIFACT EXISTS, Phase 3 = ARTIFACT EXISTS with 4 critical fixes
- SKILL.md Key Architectural Notes item 8: already contains WebSocket heartbeat protocol (server-initiated, pong response, 5 missed = disconnect)
- FUNCTION-CONTRACTS.md line 517: `open_position` Signal already includes `atr` field
- FUNCTION-CONTRACTS.md lines 289-310: `fetch_commission_rate_per_side` contract already exists

**Result**: Fixes 1, 2, 4, 5 are already applied. Only fixes 3, 7, 8, 9 remain.

---

## Remaining Fixes

### Fix 3: Add SMA note to `_compute_stochastic` docstring
- **File**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\docs\FUNCTION-CONTRACTS.md`
- **Location**: ~line 1492
- **Old**: `"Compute Raw K stochastic and D-line for last bar from bar buffer."`
- **New**: `"Compute Raw K (smooth=1) stochastic and D-line (SMA of K, not EMA) for last bar from bar buffer."`
- **Tool**: Edit

### Fix 7: Session log
- **File**: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-03-13-weex-phase2-3-audit.md` (new file)
- **Tool**: Write
- **Content**: Summary of both sessions — all 9 fixes (4 from prior session + what was already in place + Fix 3 this session), phase status, verification results

### Fix 8: INDEX.md append
- **File**: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\INDEX.md`
- **Tool**: Edit (append row)
- **Row**: `| 2026-03-13-weex-phase2-3-audit.md | WEEX Phase 2/3 Opus audit session log — all fixes applied, phase status confirmed |`

### Fix 9: PROJECT-STATUS.md update
- **File**: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\PROJECT-STATUS.md`
- **Tool**: Edit
- **Change**: Line ~130: `"WEEX connector — plan approved, no code built"` → `"WEEX connector — Phase 2+3 artifacts exist (Sonnet-built, Opus-audited, 4 critical fixes applied). Phase 4 blocked on API keys."`

---

## Fixes Already Applied (skip these)

| Fix | Status | Evidence |
|-----|--------|---------|
| Fix 1: commission_rate contract in FUNCTION-CONTRACTS.md | ALREADY DONE | Lines 289-310 contain fetch_commission_rate_per_side contract |
| Fix 2: `atr` in open_position Signal | ALREADY DONE | Line 517 includes `atr` field |
| Fix 4: Heartbeat protocol in SKILL.md | ALREADY DONE | Key Architectural Notes item 8 |
| Fix 5: Phase status in SKILL.md | ALREADY DONE | Lines 240-244 show correct status |
| Fix 6: Run command for Phase 2 | No file change needed | Tell user in response |

---

## Run Command (tell user, do NOT execute)

```
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\scripts\build_coin_index.py"
```

---

## Verification

After each edit:
1. Read back FUNCTION-CONTRACTS.md ~line 1492 — verify SMA note in `_compute_stochastic`
2. Read back INDEX.md last entry — verify row appended correctly
3. Read back PROJECT-STATUS.md WEEX line — verify updated

---

## Files Modified

| File | Tool | Action |
|------|------|--------|
| `PROJECTS/weex-connector/docs/FUNCTION-CONTRACTS.md` | Edit | Fix 3: SMA note in _compute_stochastic |
| `06-CLAUDE-LOGS/2026-03-13-weex-phase2-3-audit.md` | Write | Fix 7: New session log |
| `06-CLAUDE-LOGS/INDEX.md` | Edit | Fix 8: Append row |
| `06-CLAUDE-LOGS/PROJECT-STATUS.md` | Edit | Fix 9: Update WEEX status |
