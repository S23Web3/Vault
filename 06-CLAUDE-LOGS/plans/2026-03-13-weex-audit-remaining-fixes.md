# WEEX Phase 2/3 Opus Audit — Remaining Fixes

## Context

Continuing the WEEX Connector Phase 2/3 + Function Contracts Opus Audit. Three Sonnet-built artifacts were audited. The prior session applied critical fixes (ping/pong rename, atr_at_entry in add_position, all 4 stochastic periods). This session completes the remaining fixes and writes session documentation.

## What Was Already Fixed (verified by reading files)

- `_send_heartbeat` renamed to `_handle_server_ping` (line 1266)
- `_on_message` docstring updated to route to `_handle_server_ping()` (line 1244)
- `atr_at_entry` added to `StateManager.add_position()` (line 680, 688-689)
- All 4 stochastic constants present (9-3, 14-3, 40-3, 60-10) at lines 1424-1431
- Signal NamedTuple includes `atr` field (line 1447)

## Remaining Fixes

### Fix 1: Add `fetch_commission_rate()` contract to api_utils.py section
**File**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\docs\FUNCTION-CONTRACTS.md`
**Location**: After `_rate_limit_wait()` (line 296), before Section 4 (data_fetcher.py, line 300)
**Action**: Insert new function contract for `fetch_commission_rate(symbol: str) -> float`
- API call: `GET /capi/v3/account/commissionRate?symbol=BTCUSDT`
- Returns taker fee rate per side (e.g., 0.001)
- Caches result with TTL (one fetch per session is sufficient)
- Prevention rule: W06 (cache), W07 (explicit naming: `_per_side` suffix)
- Also add `_commission_cache` to api_utils.py variables table (after line 184)

### Fix 2: Add `atr` to Signal description in `open_position()` docstring
**File**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\docs\FUNCTION-CONTRACTS.md`
**Location**: Line 517
**Action**: Change "symbol, direction, grade, sl_price, quantity" to "symbol, direction, grade, sl_price, quantity, atr"

### Fix 3: Add SMA note to `_compute_stochastic` docstring
**File**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\docs\FUNCTION-CONTRACTS.md`
**Location**: Line 1492
**Action**: Change docstring from "Compute Raw K stochastic and D-line for last bar from bar buffer." to "Compute Raw K (smooth=1) stochastic and D-line (SMA of K, not EMA) for last bar from bar buffer."

### Fix 4: Fix ping/pong protocol in WEEX skill
**File**: `C:\Users\User\.claude\skills\weex\SKILL.md`
**Action**: Add a "WebSocket Heartbeat Protocol" section under "Key Architectural Notes" that explicitly states:
- Server sends `{"event": "ping", "time": "..."}`
- Client MUST respond `{"event": "pong", "time": "..."}`
- 5 missed pongs = disconnect
- Do NOT use client-side timer

### Fix 5: Update Phase Status in WEEX skill
**File**: `C:\Users\User\.claude\skills\weex\SKILL.md`
**Location**: Lines 240-244 (Phase Status section at end of file)
**Action**: Update Phase 2 and Phase 3 status:
- Phase 2: ARTIFACT EXISTS (build_coin_index.py — Sonnet-built, Opus-audited, ready to run)
- Phase 3: ARTIFACT EXISTS (UML + Function Contracts — Sonnet-built, Opus-audited, 4 critical fixes applied)

### Fix 6: Give Phase 2 run command
**Action**: Tell user (do NOT execute):
```
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\scripts\build_coin_index.py"
```

### Fix 7: Session log
**File**: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-03-13-weex-phase2-3-audit.md` (new — Write tool)
**Content**: Summary of audit findings, all fixes applied (prior + this session), phase status

### Fix 8: INDEX.md append
**File**: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\INDEX.md`
**Action**: Append row for the new session log

### Fix 9: PROJECT-STATUS.md update
**File**: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\PROJECT-STATUS.md`
**Action**: Update WEEX status from "plan approved, no code built" to "Phase 2+3 artifacts exist (Sonnet-built, Opus-audited, 4 critical fixes applied)"

## Verification

1. Read back FUNCTION-CONTRACTS.md lines 180-300 — verify commission_rate contract and cache variable
2. Read back FUNCTION-CONTRACTS.md line 517 — verify atr in Signal description
3. Read back FUNCTION-CONTRACTS.md line 1492 — verify SMA note
4. Read back SKILL.md — verify heartbeat section and phase status
5. Read back INDEX.md last entry — verify row appended
6. Read back PROJECT-STATUS.md WEEX line — verify updated

## Files Modified

| File | Tool | Action |
|------|------|--------|
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\docs\FUNCTION-CONTRACTS.md` | Edit | 3 edits: commission contract, Signal desc, stoch docstring |
| `C:\Users\User\.claude\skills\weex\SKILL.md` | Edit | 2 edits: heartbeat protocol, phase status |
| `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-03-13-weex-phase2-3-audit.md` | Write | New session log |
| `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\INDEX.md` | Edit | Append row |
| `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\PROJECT-STATUS.md` | Edit | Update WEEX status |
