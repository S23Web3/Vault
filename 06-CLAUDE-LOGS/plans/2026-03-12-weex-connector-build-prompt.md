# WEEX Connector — New Chat Handoff Prompt
# Date: 2026-03-12
# Do NOT execute any steps in the chat this prompt was written in.
# Paste the block below as your FIRST message in a new chat.

---

## PASTE THIS AS YOUR OPENING MESSAGE:

You are starting a multi-phase build: **WEEX Futures Trading Connector v1.0**.

Read the following context carefully before doing anything.

---

### STARTUP PROTOCOL (mandatory before anything else)

1. Read `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\PROJECT-STATUS.md`
2. Read `C:\Users\User\.claude\projects\c--Users-User-Documents-Obsidian-Vault\memory\TOPIC-bingx-connector.md`
3. Read `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-12-weex-connector-v1.md` — this is the approved architecture plan
4. Read `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-24-weex-screener-scope.md` — confirmed WEEX public API endpoints
5. Read `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-02-27-automation-weex-screener-daily-report.md` — WEEX data layer spec
6. Read `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\docs\BINGX-V2-BUG-AUDIT.md` — 19 bugs found in BingX v2, distilled into 17 prevention rules. Apply as engineering principles. Do NOT copy code from v2 or v3.

Do NOT launch explore agents to find these files. Read them directly.

---

### CONFIRMED FACTS FROM PRIOR RESEARCH (do not re-probe what is already known)

**WEEX hosts that are alive (DNS resolves):**
- `api-contract.weex.com` — futures market data (klines, contracts)
- `api-spot.weex.com` — spot market data

**WEEX hosts that are DEAD (do not try these):**
- `api.weex.com` — dead (build spec from 2026-02-02 is outdated)
- `open-api.weex.com` — dead
- `api-futures.weex.com` — dead

**WEEX public market data (confirmed working from probe):**
- Contracts list: `GET https://api-contract.weex.com/capi/v2/market/contracts`
- Klines: `GET https://api-contract.weex.com/capi/v2/market/candles?symbol=cmt_btcusdt&granularity=1m&limit=1000`
- Returns latest ~1,000 candles only. No historical pagination. Confirmed by probe script.
- Symbol format for market data: `cmt_btcusdt` (lowercase, `cmt_` prefix)
- **For the live trading connector, use `api-contract.weex.com` (futures candles). The `api-spot.weex.com` endpoint returns spot market data and is NOT used by the connector.**
- **IMPORTANT**: The exact response schema for contract klines (field names, timestamp format, OHLCV field order) is unconfirmed. Phase 1 MUST confirm this. Do NOT assume it matches the spot candles response from `api-spot.weex.com`.

**WEEX has no historical OHLCV API.** Backtesting will use Bybit data as proxy. WEEX connector uses live klines from `api-contract.weex.com` only.

**BingX data** (`data/bingx/`) covers ~626 coins. Some of these coins are NOT on Bybit. The WEEX coin list should be cross-referenced against the BingX coin list to identify any WEEX-only coins. This is a data inventory task, not a priority blocker.

---

### WEEX = Bitget White-Label (context only — NOT a shortcut)

The WEEX API is a Bitget white-label. Evidence:
- `/capi/v2/` path = Bitget contract API structure
- `/api/v2/` path = Bitget spot API structure
- `cmt_btcusdt` symbol format = Bitget contract format
- `BTCUSDT_SPBL` spot format = Bitget spot format

Bitget docs (`https://www.bitget.com/api-doc/contract/intro`) are a SECONDARY cross-reference. WEEX docs are the primary source. Use Bitget docs to sanity-check WEEX responses or fill gaps where WEEX docs are unclear. Do NOT copy Bitget API patterns wholesale — WEEX may have diverged.

**NOTE**: The screener scope doc (`2026-02-24-weex-screener-scope.md`) uses spot format (`BTCUSDT_SPBL`). Ignore for the futures connector — use `cmt_` prefix format from probe results.

---

### WHAT THE USER TRADES

**Futures (perpetual contracts) on WEEX.** Not spot. All connector logic, order placement, position management, and API endpoints must target WEEX futures/perpetuals.

---

### OPEN-SOURCE INTENT

This connector will be submitted to a public GitHub repository that collects exchange API connectors. Implications:
1. All code must be original — no copy-paste from BingX connector v2, v3, or any other source
2. Code must be well-documented, clean, and independently useful
3. The bug audit prevention rules (17 items) should be applied as engineering principles, not copied as code
4. README.md must be comprehensive: setup, config, usage, architecture
5. License-compatible (target repo not yet decided — LICENSE file deferred to Phase 8)
6. No hardcoded paths to this vault or user-specific config

---

### PHASE SEQUENCE (do these IN ORDER, do not skip ahead)

#### PHASE 0 — Load skills (mandatory before any code)
Load the Python skill: `/python`
Then create a WEEX skill SCAFFOLD at `C:\Users\User\.claude\skills\weex\SKILL.md` with known facts ONLY (base URLs, symbol formats, dead hosts). Full endpoint details will be added AFTER Phase 1 completes. See "WEEX Skill Creation" below.

---

#### PHASE 1 — Scrape WEEX API docs to reference document

The WEEX API documentation is at: `https://www.weex.com/api-doc/contract/Market_API/GetBookTicker`

The left sidebar of that page contains the full API menu. The website does NOT support deep-linking to individual sections — you must navigate the sidebar.

This task mirrors how the BingX API docs were scraped: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\scrape_bingx_docs.py` (890 lines, Playwright-based, SPA navigation via menu clicks).

**What to scrape:**
- All futures contract endpoints: Market API, Trade API, Account API, WebSocket API
- For each endpoint: method (GET/POST), URL path, all parameters (name, type, required/optional, description), response fields, authentication requirements
- Focus: futures perpetuals only (not spot)
- Output: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\docs\WEEX-API-COMPLETE-REFERENCE.md`

**Critical endpoints to find and document (navigate the left menu to locate these):**
1. Server time (for clock sync)
2. Contract/symbol list (what perps are available)
3. Klines / candlestick data
4. Ticker / mark price
5. Place order (market, limit, stop-market)
6. Cancel order
7. Query open orders
8. Query order history
9. Get positions
10. Get account balance / margin
11. Set leverage
12. Set margin mode (isolated/cross)
13. WebSocket: order fill events
14. WebSocket: position updates
15. Confirm whether WEEX API auth requires a passphrase (Bitget does — WEEX may or may not)
16. Confirm symbol format for order placement API (may differ from `cmt_` market data format)

**Auth method to document:**
- Header names (e.g. `X-API-KEY`, `X-TIMESTAMP`, `X-SIGN`)
- Signature algorithm (HMAC-SHA256 or other)
- Parameter sorting rules
- Any `recvWindow` equivalent

**Output format** — mirror the BingX reference structure at:
`C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\docs\BINGX-API-V3-REFERENCE.md`

Build a Playwright scraper script:
`C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\scripts\scrape_weex_docs.py`

Also scrape and document: **rate limits for authenticated endpoints** (may differ from the 500 req/10s public limit).

Then run the scraper and produce the reference doc. This doc is the foundation for everything else. Do not proceed to Phase 2 until it exists and is reviewed.

**SESSION BUDGET NOTE**: The BingX scraper was 890 lines of Playwright code. Phase 1 may require its own dedicated session. If the full scraper approach proves too complex, an alternative is manual navigation with Playwright MCP (`browser_navigate` + `browser_snapshot`) to extract endpoint details section by section.

**CHECKPOINT** — Do not proceed to Phase 2 until Phase 1 output is reviewed by the user.

---

#### PHASE 2 — WEEX coin inventory

Cross-reference WEEX available perps against existing data:
- Fetch WEEX contract list from `api-contract.weex.com/capi/v2/market/contracts`
- Load coin list from BingX data dir: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\data\bingx\`
- Load coin list from Bybit data dir: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\data\cache\`
- Produce a CSV: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\docs\WEEX-COIN-INDEX.csv`
  - Columns: symbol, on_weex, on_bingx, on_bybit, data_source (which dir to use for backtesting)
- Output script: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\scripts\build_coin_index.py`
- Also output a summary count (e.g., "412 WEEX perps, 380 overlap with BingX, 32 WEEX-only")

**CHECKPOINT** — Confirm with user before proceeding to Phase 3.

---

#### PHASE 3 — UML architecture

Using the API reference from Phase 1, design the full connector UML.

Model after the BingX connector UML at:
`C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\BINGX-CONNECTOR-UML.md`

**Key differences to design for:**
- WEEX auth scheme (from Phase 1 research — will differ from BingX HMAC query-param signing)
- WEEX symbol format for order API (may differ from market data `cmt_btcusdt` format)
- WEEX position mode (hedge mode vs one-way — confirm from API docs)
- WEEX WebSocket event schema (fill detection — differs from BingX)
- WEEX trailing stop order type (if supported)

**Output:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\docs\WEEX-CONNECTOR-UML.md`

Include:
- System context diagram (exchange / bot / trader / Telegram)
- Component diagram (all modules + data flows)
- Sequence diagram: trade lifecycle (entry → SL → BE raise → TTP → exit)
- Thread model (MarketLoop / MonitorLoop / WSListener)

**CHECKPOINT** — Confirm UML with user before proceeding to Phase 4.

---

#### PHASE 4 — Logic lifeline walkthrough

**BLOCKER**: User must have WEEX API keys created and funded before this phase. STOP and tell the user — do not proceed until they confirm keys are ready. See README.md instructions below.

Before writing any production code, do a logic lifeline test:

For each critical flow, write a small test script that calls the WEEX API (with real keys or sandbox if available) and verifies the response:
- `test_connection.py` — auth works, server time syncs
- `test_market_data.py` — klines fetch, symbol list, mark price
- `test_order_lifecycle.py` — place market order, check position, place SL, cancel, close
- `test_ws_fills.py` — WebSocket connects, receives fill event on test order

These tests run against live WEEX API (user will provide API keys in `.env`).
**Do NOT hardcode keys.** Read from `.env`.

`.env` location: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\.env`

`.env.example` format (write this file as part of Phase 4 setup):
```
WEEX_API_KEY=your_api_key_here
WEEX_API_SECRET=your_api_secret_here
WEEX_API_PASSPHRASE=your_passphrase_here
WEEX_TELEGRAM_TOKEN=same_as_bingx_if_same_bot
WEEX_TELEGRAM_CHAT_ID=same_as_bingx_if_same_chat
```

**Instructions for user** (write in `README.md`):
1. Go to WEEX → Account → API Management
2. Create API key with: Read + Trade permissions (no Withdraw)
3. Copy API Key and Secret
4. Paste into `weex-connector/.env`
5. Fund WEEX futures wallet with desired amount
6. Run `python scripts/test_connection.py` to verify

---

#### PHASE 5 — Function design from UML

For each module identified in the UML, write the **function signatures and docstrings only** — no implementation bodies yet.

This is the contract for the build. Every function gets:
- Name
- Parameters + types
- Return type
- One-line docstring describing what it does
- Which API endpoint it calls (if applicable)

Write to: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\docs\FUNCTION-CONTRACTS.md`

**CHECKPOINT** — Confirm function contracts with user before proceeding to Phase 6 (the full build).

---

#### PHASE 6 — Full connector build

**All files must be created via a single `build_weex_connector.py` script** (per CLAUDE.md: "SCRIPT IS THE BUILD"). The script creates all source files, py_compiles each, reports results.

Build order (one module at a time, test at each step):

1. `api_utils.py` — write original shared helpers: mark price fetch, token-bucket rate limiter for authenticated endpoints (rate limits from Phase 1 research)
2. `weex_auth.py` — signing + headers → test: signed request returns 200
3. `time_sync.py` — server time offset → test: offset < 5s
4. `data_fetcher.py` — OHLCV polling, 201-bar rolling buffer → test: fills correctly
5. `executor.py` — place market, place SL, cancel → test: lifecycle test
6. `position_monitor.py` — query positions, BE raise, TTP tighten → test: detects open position
7. `state_manager.py` — state.json + trades.csv atomic writes → test: read-write-read parity
8. `risk_gate.py` — write original, exchange-agnostic risk gate (apply bug audit prevention rules)
9. `signal_engine.py` — write original strategy adapter (apply W19 pattern: exc_info=True on plugin errors). The strategy plugin (`plugins/`) must use the **latest signal version at build time** — reimplement the algorithm from scratch as standalone code (no import from backtester repo). This is required for open-source independence.
10. `notifier.py` — write original Telegram notifier
11. `ttp_engine.py` — write original TTP engine (price-level trailing logic)
12. `ws_listener.py` — WebSocket fills → WEEX-specific WS endpoint + message parsing. Must include: exponential backoff reconnect (max 60s), ping/pong heartbeat per WEEX WS spec, connection-dead detection timeout, and thread-safe fill queue.
13. `main.py` — thread orchestration, startup sequence. Must include: (a) SIGINT/SIGTERM handler that sets shutdown flag, waits for in-flight orders, flushes state.json, logs clean shutdown. (b) Config.yaml validation at startup — check all required fields exist, types are correct, values are in valid ranges. Fail fast with clear error message.
14. `requirements.txt` — write from scratch for WEEX dependencies
15. Full test suite: `tests/` (mirror BingX 67-test structure)

**Project root:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\`

At each module: write the code → py_compile + ast.parse → run the relevant test script → only proceed when test passes.

**All modules written as original code.** Use BingX v2 (`bingx-connector-v2/`) as ARCHITECTURAL reference for component structure only. Apply the 17 bug prevention rules from `BINGX-V2-BUG-AUDIT.md` as engineering principles. Do NOT copy code from any BingX version.

**CHECKPOINT** — Full build complete. Confirm all tests pass with user before proceeding to Phase 7 (latency profiling).

---

#### PHASE 7 — Order placement latency profiling

After the full build is complete and all tests pass, measure order placement latency:

- Time the round-trip for each API call in `executor.py`: market order, SL placement, cancel, position query
- Log p50/p95/p99 latencies over 100 test calls (use testnet or paper mode if available)
- **If WEEX has no testnet**: profile only read-only endpoints (mark price, positions, open orders). Order placement latency can be measured from the single real trade lifecycle during Phase 8 live test.
- If any single call exceeds 2 seconds p95, investigate (DNS, keep-alive, connection pooling)
- Write findings to: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\docs\LATENCY-PROFILE.md`
- Do NOT profile signal computation or buffer updates — the connector polls every 45s, these are not hot paths
- Do NOT add JIT (Numba), OOP refactors, or architectural changes — premature optimization for a 45s poll loop

---

#### PHASE 8 — Complete audit + live test

- Full code audit (docstrings, commission math, SL direction, state persistence, thread safety)
- 24h paper run (if WEEX has sandbox) or live run with minimum position size
- Verify: fills detected correctly, Telegram alerts fire, state.json persists across restart
- Write audit report: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\docs\AUDIT-REPORT.md`
- Create `LICENSE` file — confirm with user which license the target GitHub repo requires (MIT, Apache 2.0, etc.)

---

### WEEX SKILL CREATION (do this in Phase 0)

Create a new skill file at:
`C:\Users\User\.claude\skills\weex\SKILL.md`

**Phase 0**: Create scaffold with known facts only (base URLs, confirmed symbol formats, dead hosts, rate limits from screener scope doc).
**After Phase 1**: Populate the skill with full endpoint details, auth method, WebSocket schema, and quirks discovered from the docs scrape.

Sections to include:
- Base URLs (confirmed live hosts only)
- Auth method (header names, signature algorithm, param order)
- Symbol format (market data vs order API — may differ)
- Key endpoints (with method, path, required params)
- Response format (wrapper structure: `{code, msg, data}` or raw list?)
- WebSocket endpoint + auth + message types
- Known quirks (rate limits, timestamp tolerance, fill detection gaps)
- Testnet/sandbox availability (yes/no, URL if yes)

Update `CLAUDE.md` to add the WEEX skill trigger rule (same pattern as Python skill and Dash skill mandatory rules). Add it after the existing DASH SKILL MANDATORY rule in CLAUDE.md.

Also create in Phase 0:
- `.gitignore` — exclude `.env`, `__pycache__/`, `logs/`, `*.pyc`, `state.json`, `trades.csv`
- `api_utils.py` scaffold — create empty module with shared HTTP helpers structure (mark price fetch + rate limiter will be populated in Phase 6, but Phase 4 test scripts need the import path to exist)

**NOTE**: `LICENSE` file deferred to Phase 8 — target GitHub repo not yet decided, so license choice is unknown.

---

### KNOWN BUGS FROM BINGX v2 — DO NOT REPEAT

A full audit was done on `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\` — 19 bugs found, distilled into 17 prevention rules. Full audit documented in:
`C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\docs\BINGX-V2-BUG-AUDIT.md`

Read that file before writing any WEEX connector code. The fixed version is at:
`C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v3\`

**BingX v2 is the architectural reference. v3 is a separate open-source project — do NOT use as template.** The 17 prevention rules below apply as engineering principles.

**Critical prevention rules (from the audit):**
1. **Single state read per check cycle** — never read `get_open_positions()` twice in the same function
2. **Deep copy all position data** — `json.loads(json.dumps(...))` pattern
3. **Never fall back to SL price** for non-SL exits — fetch mark price instead
4. **Always pass dict copies** to API retry calls
5. **Filter orders by positionSide** when attributing fills
6. **Cache exchange metadata** (contracts, step sizes) with 1h TTL
7. **Name commission variables explicitly** — `_rt` suffix for round-trip
8. **Log warnings for stuck symbols** that never produce signals
9. **Pass singletons explicitly** — no module-level global state
10. **Sort orders by timestamp**, not by orderId
11. **Send Telegram on ALL PnL-affecting state changes** (including reconcile)
12. **Throttle warmup** — 100ms minimum between fetches
13. **Use `datetime.now(timezone.utc)`** everywhere
14. **Use absolute paths** — `Path(__file__).resolve().parent`
15. **Consistent API helper contracts** — document whether helpers check error codes
16. **No duplicate utility functions** — shared code in `api_utils.py`
17. **Always log tracebacks** — `exc_info=True` on exception handlers

---

### REFERENCES AND ORIGINALITY

**Architecture reference**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\`
Use v2 as the ARCHITECTURAL reference — component structure, thread model, config schema, state management pattern. Do NOT copy code from v2 or v3.

**Bug prevention reference**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\docs\BINGX-V2-BUG-AUDIT.md`
The 17 prevention rules are engineering principles to follow. They describe PATTERNS to avoid, not code to copy.

**BingX v3** (`C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v3\`) is a SEPARATE open-source project. Do NOT use as a template. Do NOT copy files from it.

**ALL WEEX connector code must be original** — written from WEEX API docs. This connector will be submitted to a public GitHub repo and must stand on its own.

---

### HARD RULES REMINDER (non-negotiable)

- Load `/python` skill before writing ANY .py file
- py_compile + ast.parse MUST pass on every file written
- No backslash paths in strings — use `pathlib.Path`
- No bash execution of Python scripts — write the file, give the run command, stop
- Every `def` must have a one-line docstring
- Dual logging on every module (file + console, timestamps)
- Output complete builds only — no stubs, no placeholders
- NEVER overwrite files — check existence first, create versioned copy if exists
- Full Windows paths in all output and prose
- At 70% context: STOP, summarize, update MEMORY.md, tell user to open new chat

---

### REFERENCE FILES

| What | Path | Role |
|------|------|------|
| Architecture plan | `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-12-weex-connector-v1.md` | Overall design |
| BingX v2 (architecture ref) | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\` | Component structure reference |
| Bug audit | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\docs\BINGX-V2-BUG-AUDIT.md` | Prevention rules |
| BingX scraper (pattern ref) | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\scrape_bingx_docs.py` | Scraper approach |
| BingX UML | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\BINGX-CONNECTOR-UML.md` | UML structure reference |
| WEEX screener scope | `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-24-weex-screener-scope.md` | Confirmed endpoints |
| Strategy signals | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\` | Signal code |
| Python skill | `C:\Users\User\.claude\skills\python\` | Skill |

---

### START COMMAND

**Step 1 — Load skills (do FIRST, before reading files):**
```
/python
```

**Step 2 — Read ALL startup files (items 1-6 from STARTUP PROTOCOL above). Do NOT launch agents. Read directly.**

**Step 3 — Request permissions upfront (ask user to approve all at once):**
Tell the user: "I need the following permissions for this build. Please approve all at once so we can work uninterrupted:"
1. Write tool — creating new files in `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\`
2. Write tool — creating skill file at `C:\Users\User\.claude\skills\weex\SKILL.md`
3. Edit tool — editing `CLAUDE.md` to add WEEX skill trigger rule
4. Bash tool — `python -c "import py_compile; ..."` one-liners for syntax validation (per CLAUDE.md exception)
5. Bash tool — `ls` / directory checks before file creation
6. Playwright MCP tools — for Phase 1 API docs scrape (`browser_navigate`, `browser_snapshot`, `browser_click`)

**Step 4 — Confirm ready:**
**"All skills loaded, startup files read, permissions granted. Starting Phase 0: creating WEEX skill scaffold + .gitignore + api_utils.py scaffold."**

Then proceed to Phase 1 (API docs scrape). Do not skip ahead.
