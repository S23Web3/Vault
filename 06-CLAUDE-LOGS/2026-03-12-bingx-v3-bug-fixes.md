# Session Log — 2026-03-12 — BingX Connector v3 Bug Audit + Build

## What Was Done This Session

### 1. Full Bug Audit of BingX Connector v2

Read all 12 production .py files in `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\`. Identified 19 bugs categorized by severity:

- **4 CRITICAL**: Race condition double PnL (W01), TTP exit falls back to SL price (W02), shallow copy thread unsafety (W03), stale timestamp on retry (W04)
- **5 HIGH**: No positionSide filter on fill attribution (W05), no step_size caching (W06), commission rate naming confusion (W07), silent 1-bar symbols (W08), singleton ignores base_url (W09)
- **7 MEDIUM**: orderId sort unreliable (W10), no log cleanup (W11), phantom reconcile hides losses (W12), warmup no throttle (W13), deprecated utcnow (W14), relative path for dead flag (W15), inconsistent _safe_post contract (W16)
- **3 LOW**: duplicated mark price (W17), duplicated cancel SL (W18), plugin exceptions swallowed (W19)

**Output**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\docs\BINGX-V2-BUG-AUDIT.md`

### 2. BingX Connector v3 Build

Built `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v3\` — complete copy of v2 with all 19 bugs fixed. Key structural changes:
- New `api_utils.py` — shared mark price fetch (W17 fix)
- `state_manager.py` — deep copy positions, reconcile now accepts notifier+auth for Telegram alerts
- `position_monitor.py` — single state read, processed_keys tracking, positionSide filtering, timestamp-based order sorting
- `executor.py` — step_size caching, dict copy on retry, renamed _raw_post
- `main.py` — log cleanup at startup, commission_rate_rt naming
- `ws_listener.py` — absolute paths, datetime.now(timezone.utc)
- `signal_engine.py` — exc_info=True on plugin errors

All files py_compile validated.

### 3. WEEX Build Prompt Updated

Updated `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-12-weex-connector-build-prompt.md`:
- Added "KNOWN BUGS FROM BINGX v2" section with 17 prevention rules
- Added "WEEX = Bitget White-Label" critical adjustment
- Updated REFERENCE FILES table to point to v3 as template
- Changed all "copy from BingX" instructions to reference v3, not v2

### 4. Critical Finding: WEEX = Bitget White-Label

API URL patterns (`/capi/v2/`, `/api/v2/`), symbol formats (`cmt_btcusdt`, `BTCUSDT_SPBL`), and endpoint structure all match Bitget exactly. This means:
- Phase 1 (doc scraping) can use Bitget docs as primary reference
- Auth scheme is likely Bitget's (header-based HMAC)
- Bitget Python SDKs may be usable

## Files Created This Session

| File | Purpose |
|------|---------|
| `PROJECTS/weex-connector/docs/BINGX-V2-BUG-AUDIT.md` | Full 19-bug audit report with fixes |
| `PROJECTS/bingx-connector-v3/` | Bug-fixed v3 connector (all 19 fixes applied) |
| `06-CLAUDE-LOGS/2026-03-12-bingx-v3-bug-fixes.md` | This session log |

## Files Modified This Session

| File | Change |
|------|--------|
| `06-CLAUDE-LOGS/plans/2026-03-12-weex-connector-build-prompt.md` | Added bugs section, Bitget note, v3 references + 11 audit fixes (A1-A11) |
| `06-CLAUDE-LOGS/INDEX.md` | Appended this session entry |
| `06-CLAUDE-LOGS/2026-03-12-weex-connector-planning.md` | Appended v3 build reference |

## Rule Going Forward

**INDEX.md must be updated every session.** Any session that creates or modifies files MUST append an entry to `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\INDEX.md` before ending. This is now a hard rule alongside the existing MEMORY.md update rule.

### 5. Build Prompt Meta-Audit (11 fixes)

After the v3 build and bug audit were complete, audited the build prompt itself for consistency. Found and applied 11 fixes:

- **A1**: Phase 6 explicit v3 file references (not just "copy from v3")
- **A2**: Phase 0 split into skill scaffold + populate steps
- **A3**: Bug audit added to startup protocol (step 6)
- **A4**: Bitget docs URL added to white-label section
- **A5**: Passphrase field added to `.env.example`
- **A6**: Phase 7 replaced — JIT/OOP evaluation -> order placement latency profiling (45s poll loop makes JIT premature)
- **A7**: Startup file 5 verification — confirmed OK, no fix needed
- **A8**: Build script mandate added to Phase 6 (merged)
- **A9**: `api_utils.py` added to Phase 6 build order (merged)
- **A10**: Spot vs contract endpoint clarification added
- **A11**: `requirements.txt` generation added to Phase 6 (merged)

## Next Action

Open a new chat. Paste the updated contents of:
`C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-12-weex-connector-build-prompt.md`

The template is now v3 (bug-fixed), not v2.
