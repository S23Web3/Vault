# Session Log — 2026-03-12 — WEEX Build Prompt Review & Refinement

## What Was Done

Reviewed and refined `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-12-weex-connector-build-prompt.md` (the 8-phase WEEX connector handoff prompt) before execution.

### User Corrections (3 critical changes)

1. **Keep the WEEX Playwright scraper** — WEEX forked from Bitget but may have diverged. Cannot assume 1:1 copy. Scrape WEEX docs as primary source; Bitget is secondary cross-reference only.
2. **BingX v2 is the architectural reference** — v3 is a separate open-source project for later submission to a GitHub community repo.
3. **WEEX connector = original code** — not a copy or port. Written from WEEX's own API docs. Will be submitted to a public GitHub repo. Cannot be a copy of Bitget or BingX.

### 13 Edits Applied

| # | What | Why |
|---|------|-----|
| 1 | Bitget section rewritten — secondary ref, not primary | WEEX may have diverged |
| 2 | Template references — v2 architecture, no code copying | v3 is separate open-source project |
| 3 | Phase 6 — all original code, no "copy from v3" | Connector must be original for GitHub |
| 4 | Reference files table updated | Align with v2 as reference |
| 5 | Architecture plan updated | Was referencing wrong connector |
| 6 | Startup protocol updated | Removed v3 template language |
| 7 | Open-source intent section added | GitHub submission requirement |
| A | API key blocker callout in Phase 4 | Dependency not prominent |
| B | .gitignore creation added to Phase 0 | Open-source project |
| C | LICENSE file deferred to Phase 8 | Target repo unknown |
| D | Passphrase verification added to Phase 1 | Unverified Bitget pattern |
| E | Order symbol format added to Phase 1 | Unknown, critical for executor |
| F | Spot vs futures symbol clarification | Prevents confusion from screener doc |

### User's Additional Refinements (post-review)

User made further edits directly to both files:
- Added CHECKPOINT gates between all phases (user must confirm before proceeding)
- Session budget note for Phase 1 (BingX scraper was 890 lines — Phase 1 may need its own session)
- WS listener spec: exponential backoff reconnect, ping/pong heartbeat, connection-dead detection, thread-safe fill queue
- Signal plugin: must reimplement latest signal version from scratch as standalone code (no backtester import) for open-source independence
- Config validation at startup in main.py (fail fast on missing/invalid fields)
- Rate limiter in api_utils.py for authenticated endpoints
- Contract kline response schema flagged as unconfirmed (do NOT assume matches spot)
- LICENSE deferred to Phase 8 (target repo not yet decided)
- api_utils.py scaffold added to Phase 0 (Phase 4 test scripts need import path)
- Renamed plugin from `four_pillars_v384.py` to `four_pillars.py` (cleaner for open-source)

### PROJECT-STATUS.md Updated

- Line 161: Changed from "BingX v3 is the template for WEEX" to "WEEX connector = original code for open-source GitHub submission. BingX v2 = architecture reference only. v3 = separate project."
- Note: Line 12 and line 31 still reference v3 as template — these are in the BingX section, not the WEEX decision. User may want to clean up later.

## Files Modified

| File | Change |
|------|--------|
| `06-CLAUDE-LOGS/plans/2026-03-12-weex-connector-build-prompt.md` | 13 edits + user refinements |
| `06-CLAUDE-LOGS/plans/2026-03-12-weex-connector-v1.md` | Copy/port language replaced with "write original" |
| `06-CLAUDE-LOGS/PROJECT-STATUS.md` | Decision #16 updated |
| `06-CLAUDE-LOGS/plans/2026-03-12-weex-build-prompt-review.md` | Review plan (this session's analysis) |

## Next Action

Open a new chat. Paste contents of:
`C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-12-weex-connector-build-prompt.md`
(from line 10 onwards) as the first message. Begin Phase 0.
