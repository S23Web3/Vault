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

**WEEX has no historical OHLCV API.** Backtesting will use Bybit data as proxy. WEEX connector uses live klines from `api-contract.weex.com` only.

**BingX data** (`data/bingx/`) covers ~626 coins. Some of these coins are NOT on Bybit. The WEEX coin list should be cross-referenced against the BingX coin list to identify any WEEX-only coins. This is a data inventory task, not a priority blocker.

---

### WHAT THE USER TRADES

**Futures (perpetual contracts) on WEEX.** Not spot. All connector logic, order placement, position management, and API endpoints must target WEEX futures/perpetuals.

---

### PHASE SEQUENCE (do these IN ORDER, do not skip ahead)

#### PHASE 0 — Load skills (mandatory before any code)
Load the Python skill: `/python`
Then create a new WEEX skill (instructions below under "WEEX Skill Creation").

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

**Auth method to document:**
- Header names (e.g. `X-API-KEY`, `X-TIMESTAMP`, `X-SIGN`)
- Signature algorithm (HMAC-SHA256 or other)
- Parameter sorting rules
- Any `recvWindow` equivalent

**Output format** — mirror the BingX reference structure at:
`C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\docs\BINGX-API-V3-REFERENCE.md`

Build a Playwright scraper script:
`C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\scripts\scrape_weex_docs.py`

Then run the scraper and produce the reference doc. This doc is the foundation for everything else. Do not proceed to Phase 2 until it exists and is reviewed.

---

#### PHASE 2 — WEEX coin inventory

Cross-reference WEEX available perps against existing data:
- Fetch WEEX contract list from `api-contract.weex.com/capi/v2/market/contracts`
- Load coin list from BingX data dir: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\data\bingx\`
- Load coin list from Bybit data dir: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\data\cache\`
- Produce a CSV: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\docs\WEEX-COIN-INDEX.csv`
  - Columns: symbol, on_weex, on_bingx, on_bybit, data_source (which dir to use for backtesting)
- Output script: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\scripts\build_coin_index.py`

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

---

#### PHASE 4 — Logic lifeline walkthrough

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

---

#### PHASE 6 — Full connector build

Build order (one module at a time, test at each step):

1. `weex_auth.py` — signing + headers → test: signed request returns 200
2. `time_sync.py` — server time offset → test: offset < 5s
3. `data_fetcher.py` — OHLCV polling, 201-bar rolling buffer → test: fills correctly
4. `executor.py` — place market, place SL, cancel → test: lifecycle test
5. `position_monitor.py` — query positions, BE raise, TTP tighten → test: detects open position
6. `state_manager.py` — state.json + trades.csv atomic writes → test: read-write-read parity
7. `risk_gate.py` — 8 checks (copy from BingX, exchange-agnostic) → copy unchanged
8. `signal_engine.py` — strategy adapter → copy from BingX unchanged
9. `notifier.py` — Telegram alerts → copy from BingX unchanged
10. `ttp_engine.py` — TTP candle evaluation → copy from BingX unchanged
11. `ws_listener.py` — WebSocket fills → WEEX-specific WS endpoint + message parsing
12. `main.py` — thread orchestration, startup sequence
13. Full test suite: `tests/` (mirror BingX 67-test structure)

**Project root:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\`

At each module: write the code → py_compile + ast.parse → run the relevant test script → only proceed when test passes.

**Reuse from BingX (copy these unchanged):**
- `risk_gate.py` — exchange-agnostic
- `signal_engine.py` — strategy-agnostic
- `notifier.py` — only Telegram, no exchange calls
- `ttp_engine.py` — price-level logic only
- `plugins/four_pillars_v384.py` — strategy plugin

---

#### PHASE 7 — Performance review (JIT / OOP evaluation)

After the full build is complete and all tests pass, do a performance analysis:

- Profile the hot paths: OHLCV buffer update, signal computation, order placement latency
- Evaluate whether Numba JIT (`@njit`) would benefit the signal computation loop (same question was answered for the backtester — CUDA sweep exists at `engine/cuda_sweep.py`)
- Evaluate whether the current class-based architecture is the right fit or if functional/procedural would reduce complexity
- Write findings to: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\docs\PERFORMANCE-REVIEW.md`
- Only refactor if there is a clear, measurable benefit. Do not refactor speculatively.

---

#### PHASE 8 — Complete audit + live test

- Full code audit (docstrings, commission math, SL direction, state persistence, thread safety)
- 24h paper run (if WEEX has sandbox) or live run with minimum position size
- Verify: fills detected correctly, Telegram alerts fire, state.json persists across restart
- Write audit report: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\docs\AUDIT-REPORT.md`

---

### WEEX SKILL CREATION (do this in Phase 0)

Create a new skill file at:
`C:\Users\User\.claude\skills\weex\SKILL.md`

The skill should capture everything learned from the WEEX API docs scrape (Phase 1). Structure it like the BingX connector knowledge in `TOPIC-bingx-connector.md` but formatted as a skill.

Sections to include:
- Base URLs (confirmed live hosts only)
- Auth method (header names, signature algorithm, param order)
- Symbol format (market data vs order API — may differ)
- Key endpoints (with method, path, required params)
- Response format (wrapper structure: `{code, msg, data}` or raw list?)
- WebSocket endpoint + auth + message types
- Known quirks (rate limits, timestamp tolerance, fill detection gaps)
- Testnet/sandbox availability (yes/no, URL if yes)

Update `CLAUDE.md` to add the WEEX skill trigger rule (same pattern as Python skill and Dash skill mandatory rules).

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

| What | Path |
|------|------|
| Architecture plan | `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-12-weex-connector-v1.md` |
| BingX connector (template) | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\` |
| BingX API reference | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\docs\BINGX-API-V3-REFERENCE.md` |
| BingX UML | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\BINGX-CONNECTOR-UML.md` |
| BingX scraper (template) | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\scrape_bingx_docs.py` |
| WEEX screener scope | `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-24-weex-screener-scope.md` |
| Bybit data dir | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\data\cache\` |
| BingX data dir | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\data\bingx\` |
| Strategy signals | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\` |
| Python skill | `C:\Users\User\.claude\skills\python\` |

---

### START COMMAND

After reading all startup files and loading `/python`, begin with:

**"I have read all startup files. Starting Phase 0: loading Python skill and creating WEEX skill scaffold."**

Then proceed to Phase 1 (API docs scrape). Do not skip ahead.
