# WEEX Connector Build Prompt — Audit & Improvement Review (Round 2)

## Context

The build prompt at `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-12-weex-connector-build-prompt.md` was already reviewed once — see `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-12-weex-build-prompt-review.md` (v2 review). That review's 7 edits + 6 logic fixes have already been applied to the build prompt.

This is a **second-pass audit** catching issues the first review missed. 9 new findings.

---

## Verdict: First review fixes applied, 9 remaining issues

The prompt is thorough after the v2 review fixes. Phase ordering is correct, bug prevention rules are integrated, open-source constraints are clear. The issues below are net-new — not covered by the prior review.

---

## CRITICAL (will cause build failures or wrong code)

### 1. Symbol format ambiguity — futures candles endpoint unconfirmed
- **Line 41-44**: States klines use `api-contract.weex.com/capi/v2/market/candles?symbol=cmt_btcusdt`
- **Screener scope doc** (line 42): Shows candles on `api-spot.weex.com/api/v2/market/candles?symbol=BTCUSDT_SPBL`
- **Problem**: The probe confirmed `cmt_btcusdt` works for contract candles, but the screener scope doc used the spot endpoint with a different format. These are two different APIs returning different data (spot vs futures OHLCV). The build prompt correctly says "use `api-contract.weex.com`" but doesn't acknowledge that the kline endpoint response format on the contract host may differ from the spot host.
- **Fix**: Add a note: "Phase 1 must confirm the exact response schema for `api-contract.weex.com` klines (field names, timestamp format, OHLCV field order). Do not assume it matches the spot candles response."

### 2. Plugin strategy version mismatch
- **Line 66 of v1 plan**: `plugins/four_pillars_v384.py`
- **Screener scope doc** (line 57): References `compute_signals_v383`
- **Build prompt Phase 6 step 9**: `signal_engine.py` — "write original strategy adapter"
- **Problem**: Is the plugin v3.8.3 or v3.8.4? And does "write original" mean reimplement the algorithm from scratch (regression risk) or write an original adapter that imports from the backtester's signals module?
- **Fix**: Clarify: (a) which signal version, and (b) whether the plugin reimplements the algorithm or wraps an import of `compute_signals_v383` from the backtester. If open-source submission requires standalone code, the plugin must reimplement — but that should be explicit.

### 3. Bug count inconsistency: "19 bugs" vs "17 prevention rules"
- **Line 23**: "19 bugs found in BingX v2"
- **Line 316-334**: Lists "17 prevention rules"
- **Audit doc**: Lists W01-W19 (19 bugs), but W17/W18 are LOW (code quality) and were folded into rules 15/16
- **Not actually wrong** — but an executing agent may get confused searching for "19 rules" when only 17 are listed.
- **Fix**: Change line 23 to "19 bugs found, distilled into 17 prevention rules" for clarity.

---

## HIGH (will cause mid-build blocks or wasted effort)

### 4. Phase 1 scraper is a major sub-project — no session budget
- The BingX scraper is 890 lines / 37KB of Playwright code navigating a SPA sidebar
- The build prompt treats Phase 1 as one step: "build a scraper, run it, produce the doc"
- **Reality**: This is 1-2 full sessions by itself. SPA doc sites have dynamic loading, lazy rendering, and menu trees that need careful Playwright navigation
- **Fix**: Add a note: "Phase 1 may require its own dedicated session. If the scraper approach proves too complex, an alternative is manual navigation with Playwright MCP (browser_navigate + browser_snapshot) to extract endpoint details section by section."

### 5. No explicit phase gates / checkpoints
- The prompt says "do not proceed to Phase 2 until Phase 1 is reviewed" (line 137) — good
- But Phases 2-8 have no similar gates. Phase 4 has a blocker note about API keys but no "STOP and tell the user" instruction
- **Fix**: Add to each phase boundary: "CHECKPOINT — Confirm with user before proceeding to next phase." Especially critical at Phase 4 (needs API keys) and Phase 6 (full build — longest phase).

### 6. WebSocket reconnection strategy missing
- Phase 6 step 12: `ws_listener.py` — "WEEX-specific WS endpoint + message parsing"
- No mention of: reconnect backoff, heartbeat/ping handling, dead connection detection
- Bug audit W01 (race condition) involves WS fills — reconnection gaps are a related concern
- **Fix**: Add to Phase 6 step 12: "Must include: exponential backoff reconnect (max 60s), ping/pong heartbeat per WEEX WS spec, connection-dead detection timeout, and thread-safe fill queue (same pattern as BingX but original implementation)."

### 7. Target GitHub repo not named
- Line 75: "submitted to a public GitHub repository that collects exchange API connectors"
- Line 302: "user to confirm which license the target GitHub repo uses"
- **Problem**: The executing agent can't check the repo's license, README conventions, or submission format without knowing which repo
- **Fix**: User should name the target repo, or remove the license step from Phase 0 and defer to Phase 8.

---

## MEDIUM (improvements for clarity and robustness)

### 8. `api_utils.py` ordering — listed as Phase 6 step 1 but needed earlier
- Phase 4 test scripts (`test_connection.py`, `test_market_data.py`) will need shared HTTP helpers
- `api_utils.py` should exist before Phase 4, not Phase 6
- **Fix**: Move `api_utils.py` creation to Phase 0 scaffold or Phase 3 (UML), with mark price fetch added in Phase 6.

### 9. No graceful shutdown handling mentioned
- BingX connector presumably handles SIGINT/SIGTERM in main.py
- The build prompt doesn't mention signal handling, thread cleanup, or state flush on shutdown
- **Fix**: Add to Phase 6 step 13 (main.py): "Must include: SIGINT/SIGTERM handler that (1) sets shutdown flag, (2) waits for in-flight orders to complete, (3) flushes state.json, (4) logs clean shutdown."

### 10. Phase 7 latency profiling assumes testnet exists
- Line 266: "use testnet or paper mode"
- Line 76 of v1 plan: "WEEX testnet availability unknown"
- If no testnet, 100 real order calls = 100 real trades with real money
- **Fix**: Add: "If WEEX has no testnet, profile only read-only endpoints (mark price, positions, open orders). Order placement latency can be measured from a single real trade lifecycle during Phase 8 live test."

### 11. Config validation not mentioned
- `config.yaml` has many fields with specific constraints (leverage 1-125, margin_mode ISOLATED/CROSS, etc.)
- No validation step — a typo in config could cause silent misbehavior
- **Fix**: Add to Phase 6 step 13 (main.py startup): "Validate config.yaml at startup — check all required fields exist, types are correct, values are in valid ranges. Fail fast with clear error message."

### 12. Rate limit handling for authenticated endpoints
- Screener scope doc: 500 req/10s for public endpoints
- Authenticated endpoints may have different (likely stricter) limits
- No rate limiter mentioned in the build prompt
- **Fix**: Add to Phase 1 scrape targets: "Document rate limits for authenticated endpoints separately." Add to Phase 6: "Implement a simple token-bucket or sliding-window rate limiter in `api_utils.py`."

---

## MINOR (nice-to-have, not blocking)

- **Line 298**: "Update CLAUDE.md to add the WEEX skill trigger rule" — good, but specify where in CLAUDE.md (after the Dash skill rule).
- **Phase 2 coin inventory**: Could also output a summary count (e.g., "412 WEEX perps, 380 overlap with BingX, 32 WEEX-only") in addition to the CSV.
- **No mention of config hot-reload**: Adding/removing coins requires restart. Not critical for v1 but worth noting as a known limitation.

---

## Summary of Recommended Changes

| # | Severity | Change |
|---|----------|--------|
| 1 | CRITICAL | Clarify futures kline response schema must be confirmed in Phase 1 |
| 2 | CRITICAL | Specify signal version (v383 vs v384) and whether plugin reimplements or wraps import |
| 3 | CRITICAL | Fix "19 bugs" / "17 rules" phrasing |
| 4 | HIGH | Add session budget note for Phase 1 scraper |
| 5 | HIGH | Add CHECKPOINT gates at each phase boundary |
| 6 | HIGH | Add WebSocket reconnection requirements to Phase 6 |
| 7 | HIGH | Name the target GitHub repo or defer license choice |
| 8 | MEDIUM | Move `api_utils.py` creation earlier |
| 9 | MEDIUM | Add graceful shutdown requirements |
| 10 | MEDIUM | Add testnet fallback plan for latency profiling |
| 11 | MEDIUM | Add config.yaml validation step |
| 12 | MEDIUM | Add authenticated rate limit research + rate limiter |

---

## User Decisions (from Q&A)

1. **Signal version**: Use whatever is latest at build time. The build prompt should say "latest signal version" not a hardcoded version number.
2. **Plugin mode**: Reimplement from scratch — standalone, no dependency on backtester repo.
3. **Target repo**: Not decided yet — defer license to Phase 8.
4. **Action**: Apply all 12 fixes directly to the build prompt file.

---

## Execution Plan

Apply edits to `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-12-weex-connector-build-prompt.md`:

1. **Fix #1** (line ~41-44): Add note about confirming contract kline response schema in Phase 1
2. **Fix #2** (line ~66 in v1 plan, line ~242 in build prompt): Change plugin filename to generic `four_pillars_latest.py`, add note: "Use latest signal version at build time. Reimplement algorithm from scratch — standalone, no backtester import."
3. **Fix #3** (line 23): Change "19 bugs" to "19 bugs found, distilled into 17 prevention rules"
4. **Fix #4** (after line 137): Add session budget note for Phase 1
5. **Fix #5** (end of each phase): Add CHECKPOINT gates
6. **Fix #6** (Phase 6 step 12): Add WebSocket reconnection requirements
7. **Fix #7** (line 302): Remove LICENSE from Phase 0, defer to Phase 8
8. **Fix #8** (Phase 6 step 1): Move `api_utils.py` to Phase 0 scaffold
9. **Fix #9** (Phase 6 step 13): Add graceful shutdown requirements
10. **Fix #10** (Phase 7): Add testnet fallback plan
11. **Fix #11** (Phase 6 step 13): Add config validation
12. **Fix #12** (Phase 1 + Phase 6): Add authenticated rate limit research + rate limiter

Also update `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-12-weex-connector-v1.md`:
- Change `plugins/four_pillars_v384.py` to `plugins/four_pillars_latest.py`
- Add note about standalone reimplementation

---

## Verification

After applying fixes, re-read the build prompt end-to-end and confirm:

- Every phase has a clear entry condition, deliverable, and exit gate
- No version numbers conflict between sections
- Every file mentioned in Phase 6 build order is also in the Files to Create table
- The 17 prevention rules are referenced by number where relevant in Phase 6 steps
- Plugin references say "latest version" not a hardcoded number
- LICENSE is in Phase 8, not Phase 0
- Phase 1 has session budget note and rate limit research added
