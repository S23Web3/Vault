# WEEX Connector — Phase 2 + Phase 3 + Build Audit Handoff Prompt
# Date: 2026-03-13
# Paste the block below as your FIRST message in a new chat.

---

## PASTE THIS AS YOUR OPENING MESSAGE:

You are continuing the **WEEX Futures Trading Connector v1.0** build.
Phase 0 and Phase 1 are COMPLETE. This session covers Phase 2, Phase 3, and a full pre-build audit.

---

### STARTUP PROTOCOL (mandatory before anything else)

1. Load skills first — do these in a single message:
   `/weex`
   `/python`

2. Read these files directly (do NOT launch explore agents):
   - `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\PROJECT-STATUS.md`
   - `C:\Users\User\.claude\skills\weex\SKILL.md` — WEEX skill (fully populated, read this carefully)
   - `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\docs\WEEX-API-COMPLETE-REFERENCE.md` — full V3 API reference
   - `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-12-weex-connector-build-prompt.md` — master build spec (phases 0-8)
   - `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\docs\BINGX-V2-BUG-AUDIT.md` — 17 prevention rules

3. Check existing project structure:
   `ls "C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\"`

---

### CONFIRMED FACTS (do not re-research)

**API Version**: V3. Path prefix: `/capi/v3/`
**REST base**: `https://api-contract.weex.com`
**WS Public**: `wss://ws-contract.weex.com/v2/ws/public`
**WS Private**: `wss://ws-contract.weex.com/v2/ws/private`

**Symbol format MISMATCH (CRITICAL)**:
- REST V3 endpoints: `BTCUSDT` (no prefix, uppercase)
- WS push data `contractId` field: `cmt_btcusdt` (V2 format)
- Convert: strip `cmt_` prefix, uppercase

**Auth headers**: `ACCESS-KEY`, `ACCESS-SIGN`, `ACCESS-PASSPHRASE`, `ACCESS-TIMESTAMP`
**Passphrase**: Required (Bitget white-label)
**REST signing** (to verify at Phase 4): `base64(hmac_sha256(secret, timestamp + METHOD + path + body))`
**WS signing**: `base64(hmac_sha256(secret, timestamp + "/v2/ws/private"))`

**No TRAILING_STOP_MARKET** — TTP must be candle-level engine
**SL orders**: `POST /capi/v3/algoOrder` with `type: STOP_MARKET`, field `clientAlgoId` (not `newClientOrderId`)
**Position mode**: Use SEPARATED (hedge) — LONG/SHORT independent positions
**Leverage**: Set `isolatedLongLeverage` + `isolatedShortLeverage` independently in isolated SEPARATED mode
**Step size**: From `quantityPrecision` field in `/capi/v3/market/exchangeInfo` response

---

### TASK 1 — PHASE 2: Coin Inventory Script

**Goal**: Cross-reference WEEX perps against existing BingX and Bybit data.

Build script: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\scripts\build_coin_index.py`
Output script: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\scripts\build_coin_index_runner.py`
Output CSV: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\docs\WEEX-COIN-INDEX.csv`

**What to build**:
1. Fetch WEEX contract list: `GET https://api-contract.weex.com/capi/v3/market/exchangeInfo`
   - Extract all `symbols[]` where `forwardContractFlag: true` (USDT-margined perps)
   - Record: symbol, quantityPrecision, pricePrecision, minOrderSize, maxLeverage, takerFeeRate
2. Load BingX coin list from: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\data\bingx\`
   - List all `.parquet` files, extract symbol names
3. Load Bybit coin list from: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\data\cache\`
   - List all `.parquet` files, extract symbol names
4. Cross-reference and write CSV with columns:
   `symbol, on_weex, on_bingx, on_bybit, data_source, quantityPrecision, pricePrecision, minOrderSize, maxLeverage, takerFeeRate`
   - `data_source`: "bybit" if on Bybit, "bingx" if BingX-only, "none" if WEEX-only
5. Print summary: total WEEX perps, overlap with BingX, overlap with Bybit, WEEX-only count

**Rules**:
- py_compile + ast.parse on all output files
- Dual logging (file + console, timestamps)
- Every def has docstring
- Use `pathlib.Path` for all paths
- No bash execution — write the script, give run command, stop

**CHECKPOINT**: Show user the summary counts and CSV before proceeding to Phase 3.

---

### TASK 2 — PHASE 3: Full UML Architecture

**Goal**: Design the complete connector architecture BEFORE writing any production code.
The UML must be thorough enough to serve as the implementation specification.

Output: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\docs\WEEX-CONNECTOR-UML.md`

**Reference**: BingX UML at `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\BINGX-CONNECTOR-UML.md`

**Diagrams to include**:

#### 1. System Context Diagram
Show: Exchange (WEEX API), Connector Bot, Trader (Telegram alerts), Config (YAML + .env), State Files (state.json + trades.csv)

#### 2. Module/Component Diagram
Every module, its responsibility, and data flows between modules.

Modules to include (ALL of these, based on build spec):
- `main.py` — startup, config validation, thread orchestration, graceful shutdown
- `weex_auth.py` — signing, headers, request building
- `time_sync.py` — server time offset, synced timestamp
- `data_fetcher.py` — OHLCV polling, 201-bar rolling buffer, new-bar detection
- `executor.py` — place market order, place SL (algoOrder), cancel order, close position
- `position_monitor.py` — query positions, BE raise, TTP tighten post-activation, cleanup orphans
- `state_manager.py` — state.json atomic reads/writes, trades.csv append, position lifecycle
- `risk_gate.py` — 8 checks: ATR ratio, max positions, daily trades, daily loss, cooldown, etc.
- `signal_engine.py` — call strategy plugin, handle plugin errors, signal dispatch
- `notifier.py` — Telegram HTML messages, all alert types
- `ttp_engine.py` — candle-level TTP evaluation (no exchange trailing stop)
- `ws_listener.py` — WS connection, auth, heartbeat, fill event parsing, fill queue
- `api_utils.py` — shared helpers: mark price fetch, rate limiter, http helpers
- `plugins/four_pillars.py` — strategy plugin implementing StrategyPlugin ABC
- `config.yaml` — runtime config schema
- `.env` — API keys

#### 3. Thread Model Diagram
Three daemon threads + their responsibilities and synchronization:
- `MarketLoop` (data_fetcher + signal_engine) — 45s poll, new-bar detection, signal check
- `MonitorLoop` (position_monitor) — 30s check, BE/TTP/orphan cleanup
- `WSListener` (ws_listener) — async fill events, fill_queue
- Shared state: `state_manager.state_lock` (threading.Lock)
- Fill queue: thread-safe queue.Queue between WSListener and MonitorLoop

#### 4. Sequence Diagram: Full Trade Lifecycle
Show every step from signal to exit:
```
Entry -> place MARKET order -> confirm fill (WS) -> record position (state.json)
  -> place STOP_MARKET SL (algoOrder) -> confirm SL active
  -> [price moves] -> BE raise trigger -> cancel SL -> place new SL at BE price
  -> [TTP activation] -> candle-level trail starts (ttp_engine)
  -> [exit] -> WS fill event -> detect close -> compute PnL -> append trades.csv -> Telegram alert
```

Include: error paths (order fails, WS drops, SL cancel fails)

#### 5. Data Flow Diagram: State Management
Show how `state.json` is read/written across threads:
- Lock acquisition pattern
- Deep copy pattern (prevent W03 shallow copy bug)
- What gets written at each event (entry, BE raise, TTP activation, exit)
- trades.csv append sequence

#### 6. WEEX-Specific Differences from BingX
A table showing every architectural decision that differs from BingX connector:
| Concern | BingX | WEEX |
|---------|-------|------|
| Auth | HMAC query params | Header-based (ACCESS-KEY/SIGN/PASSPHRASE/TIMESTAMP) |
| Symbol format | BTC-USDT | BTCUSDT (REST) / cmt_btcusdt (WS) |
| SL order type | STOP_MARKET | algoOrder STOP_MARKET (separate endpoint) |
| Step size source | contracts list separate fetch | quantityPrecision in exchangeInfo |
| Trailing stop | TRAILING_STOP_MARKET native | Candle-level TTP engine only |
| Position query | positionSide field | side field (LONG/SHORT) |
| Leverage setting | single call | isolatedLongLeverage + isolatedShortLeverage both required |
| WS fill event path | ORDER_TRADE_UPDATE.o | msg.data.orderFillTransaction[] |
| WS symbol ID | symbol field | contractId field (cmt_ format) |
| Client order ID field | newClientOrderId | newClientOrderId (entry) / clientAlgoId (SL/conditional) |

**CHECKPOINT**: Confirm UML with user before proceeding to build audit.

---

### TASK 3 — PRE-BUILD AUDIT: Function Contracts + Variable Map

**Goal**: Before writing any production code, define EVERY function signature, docstring, and key variable in EVERY module. This is Phase 5 from the build spec, executed here before Phase 6.

This is the build contract. Every function gets:
- Name (snake_case)
- Parameters with types and descriptions
- Return type and description
- One-line docstring
- Which API endpoint it calls (if applicable)
- Which bug prevention rule(s) it relates to (from the 17-rule list)
- Thread safety note (if applicable)

Every module's KEY VARIABLES get documented:
- Name
- Type
- Scope (instance vs module vs local)
- Purpose
- Thread safety (locked / read-only / thread-local)

Output: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\docs\FUNCTION-CONTRACTS.md`

**Modules to cover (in this order)**:
1. `weex_auth.py` — signing helpers
2. `time_sync.py` — clock sync
3. `api_utils.py` — shared HTTP, mark price, rate limiter
4. `data_fetcher.py` — OHLCV buffer, new-bar detection
5. `executor.py` — order placement, SL management
6. `position_monitor.py` — position queries, BE raise, TTP tighten, orphan cleanup
7. `state_manager.py` — state.json lifecycle, trades.csv
8. `risk_gate.py` — all 8 checks
9. `signal_engine.py` — plugin dispatch, error handling
10. `notifier.py` — all Telegram message types
11. `ttp_engine.py` — candle-level TTP evaluation
12. `ws_listener.py` — WS connection lifecycle, heartbeat, fill parsing
13. `main.py` — startup sequence, thread launch, shutdown handler
14. `plugins/four_pillars.py` — StrategyPlugin implementation

**For each function, use this format**:
```markdown
#### `function_name(param1: Type, param2: Type) -> ReturnType`
**Module**: module_name.py
**Docstring**: One-line description.
**Parameters**:
- `param1` (Type): What it is and where it comes from
- `param2` (Type): What it is and constraints
**Returns**: What is returned and what it represents
**API call**: `GET /capi/v3/...` (if applicable)
**Prevention rules**: W01 (single state read), W03 (deep copy), etc.
**Thread safety**: Acquires state_lock / read-only / not shared
```

**For each module's key variables**:
```markdown
### Variables: module_name.py
| Variable | Type | Scope | Purpose | Thread Safety |
|----------|------|-------|---------|---------------|
| `_state` | dict | instance | Current open positions | Protected by state_lock |
| `_offset_ms` | int | instance | Server time offset | Read-only after sync |
```

**CHECKPOINT**: Confirm function contracts with user before Phase 6 (actual build).

---

### WEEX-SPECIFIC PATTERNS TO ENFORCE

These must appear in the function contracts and later in the build:

**SL placement pattern** (not on entry order, always separate algoOrder):
```
place_entry_order() -> get orderId -> confirm fill via WS ->
place_sl_order() with algoOrder STOP_MARKET -> store algo_order_id in state
```

**Cancel SL pattern** (place-then-cancel, per W18 / prevention):
```
place_new_sl() -> confirm success -> cancel_old_sl()
# Never cancel-then-place (naked position window)
```

**Symbol conversion** (REST <-> WS):
```python
def contractid_to_symbol(contract_id: str) -> str:
    """Convert WS contractId (cmt_btcusdt) to REST symbol (BTCUSDT)."""
    return contract_id.replace("cmt_", "").upper()
```

**Leverage setup at position open** (required before entry in SEPARATED isolated):
```
set_leverage(symbol, isolatedLongLeverage=X, isolatedShortLeverage=X)
set_margin_mode(symbol, marginType=ISOLATED, separatedType=SEPARATED)
# Only if not already set — cache the current config
```

---

### HARD RULES REMINDER

- Load `/weex` and `/python` skills before ANY code
- py_compile + ast.parse on every .py file written
- No backslash paths in strings — use `pathlib.Path`
- No bash execution of Python scripts
- Every `def` must have a one-line docstring
- Dual logging (file + console, timestamps) on every module
- NEVER overwrite files — check existence first
- Full Windows paths in all output and prose
- At 70% context: STOP, summarize, update MEMORY.md, tell user to open new chat

---

### REFERENCE FILES

| What | Path |
|------|------|
| API reference | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\docs\WEEX-API-COMPLETE-REFERENCE.md` |
| Build prompt (phases 0-8) | `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-12-weex-connector-build-prompt.md` |
| Bug audit (17 rules) | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\docs\BINGX-V2-BUG-AUDIT.md` |
| BingX v2 (arch ref) | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\` |
| BingX UML (pattern ref) | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\BINGX-CONNECTOR-UML.md` |
| Session log | `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-03-13-weex-phase0-phase1.md` |

---

### START COMMAND

Step 1 — Load skills (single message, both at once):
```
/weex
/python
```

Step 2 — Read ALL startup files listed above. Do NOT launch agents.

Step 3 — Request permissions upfront:
Tell user: "I need the following permissions for this session. Please approve all at once:"
1. Write tool — new files in `PROJECTS\weex-connector\scripts\`
2. Write tool — new files in `PROJECTS\weex-connector\docs\`
3. Bash tool — `python -c "import py_compile; ..."` for syntax validation
4. Bash tool — `ls` directory checks before file creation
5. Bash tool — read parquet file listings in `data\bingx\` and `data\cache\`

Step 4 — Execute in order:
1. Phase 2: coin inventory script (build + give run command, await results)
2. Phase 3: UML document (write to docs/)
3. Build Audit: function contracts document (write to docs/)

**Do not skip ahead. Each task has a CHECKPOINT requiring user confirmation before proceeding.**
