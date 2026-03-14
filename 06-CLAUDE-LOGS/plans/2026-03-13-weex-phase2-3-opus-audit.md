# WEEX Connector Phase 2 + Phase 3 + Function Contracts — Opus Audit

## Context

Sonnet created three artifacts for the WEEX connector build (Phase 2, Phase 3, Task 3) without being asked to — user wants Opus to do the audit. The three files are:

1. `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\scripts\build_coin_index.py` — Phase 2 coin inventory script
2. `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\docs\WEEX-CONNECTOR-UML.md` — Phase 3 UML architecture
3. `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\docs\FUNCTION-CONTRACTS.md` — Task 3 function contracts

**Goal**: Audit all three artifacts against the audit prompt spec (`C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-13-weex-phase2-3-audit-prompt.md`), the API reference, the 17 bug prevention rules, and the build spec. Produce findings with severity ratings and corrective actions.

---

## Audit Findings

### Artifact 1: `build_coin_index.py` (Phase 2)

**STATUS: MOSTLY GOOD — 4 issues**

| # | Severity | Finding | Fix |
|---|----------|---------|-----|
| P2-1 | MEDIUM | Uses V3 exchangeInfo URL (`/capi/v3/market/exchangeInfo`) which is correct per API docs. The build spec line 151 says `v2/market/contracts` which is the old probe endpoint. Sonnet correctly used V3. | No fix needed — Sonnet made the right call here. |
| P2-2 | LOW | `forwardContractFlag` field used to filter USDT-margined perps — matches API reference (line 144 of WEEX-API-COMPLETE-REFERENCE.md). Correct. | None. |
| P2-3 | LOW | Missing `takerFeeRate` extraction — the API response shows this at the symbol level (`"takerFeeRate": 0.001`), script captures it correctly via `sym.get("takerFeeRate", "")`. | None. |
| P2-4 | MEDIUM | Script uses `urllib.request` — adequate for a one-off data inventory script. No auth needed (public endpoint). Acceptable. | None. |
| P2-5 | LOW | No `--dry-run` or output path override CLI arg. Minor — acceptable for a utility script. | Optional enhancement. |
| P2-6 | **MEDIUM** | `minOrderSize` extraction: `sym.get("minQty", sym.get("minOrderSize", ""))` — the API reference shows the field as `minOrderSize` (line 149). The fallback to `minQty` is cautious but may mask a schema mismatch. Should confirm at runtime which field name is used. | Document that field name should be verified at runtime. |

**Script verdict**: Ready to run. Give user the run command, await results.

---

### Artifact 2: `WEEX-CONNECTOR-UML.md` (Phase 3)

**STATUS: GOOD — 7 issues, 2 are significant**

| # | Severity | Finding | Fix |
|---|----------|---------|-----|
| U-1 | **HIGH** | Missing diagram: **Data Flow Diagram for State Management** (Section 5 in audit prompt, lines 144-150). The UML does include state management detail inline within the sequence diagram and a separate "Data Flow Diagram: State Management" section at Section 5. Verified present — covers lock pattern, deep copy, what gets written at each event, trades.csv append, atomic write. **Actually present — no issue.** | None. |
| U-2 | **HIGH** | Missing from audit prompt spec: The heartbeat is documented as "send ping every 20s" in the UML (line 80, 217). But the API reference (line 87-88) says the SERVER sends `{"event": "ping"}` and the CLIENT must respond with `{"event": "pong"}`. The UML says `ws_listener.heartbeat() -> send ping every 20s` which implies CLIENT sends ping — this is backwards. WEEX heartbeat is server-initiated. | Fix UML Section 3 to show: server sends ping, client responds pong. WSListener._on_message must detect `{"event":"ping"}` and reply `{"event":"pong"}`. Not a separate heartbeat timer. |
| U-3 | MEDIUM | Module Responsibilities table (line 154-169) lists `api_utils.py` with `contractid_to_symbol()` — correct. But `api_utils.py` in Phase 0 already exists as an empty scaffold. The UML should note that the existing scaffold will be replaced. | Minor — document in build notes. |
| U-4 | MEDIUM | Thread Model diagram shows `fill_queue.get_nowait()` in MonitorLoop. The audit prompt (line 200) says MonitorLoop does `fill_queue.get_nowait()` — matches. Correct. | None. |
| U-5 | LOW | State schema in UML (line 228-248) includes `entry_time: int (unix ms)`, `client_order_id: str`. These match the audit prompt requirements. Correct. | None. |
| U-6 | **MEDIUM** | The WEEX-Specific Differences table (Section 6, lines 493-518) is comprehensive — 18 rows covering all key differences. One concern: row for "WS auth path string" says `"/v2/ws/private" hardcoded in sign message` — correct per API docs. However, the table says BingX uses `/openApi/swap/listen-key` flow, which is not a signing path but a listen key creation endpoint. This comparison is somewhat misleading but not wrong. | Clarify BingX column wording. |
| U-7 | LOW | Module Dependency Graph (lines 521-561) is clean and shows all dependencies. `plugins/four_pillars.py` correctly shows `(no internal imports — pure signal logic)`. | None. |
| U-8 | **HIGH** | The ping/pong protocol is inverted. The WEEX API docs (SKILL.md line 87-88) clearly state: **Server sends** `{"event": "ping", "time": ...}`, **Client must respond** `{"event": "pong", "time": ...}`. 5 missed pongs = disconnect. The UML shows `ws_listener.heartbeat() -> send ping every 20s` which implies the client initiates the ping, not the server. This will cause disconnect if not corrected — the client needs to RESPOND to server pings, not send its own. | Fix: Remove client heartbeat timer. Add _on_message handler for `event: "ping"` that sends `{"event": "pong", "time": same_time}`. This is the same as U-2 — counted once. |

**UML verdict**: Good architecture. One critical fix needed (ping/pong direction). Otherwise solid.

---

### Artifact 3: `FUNCTION-CONTRACTS.md` (Task 3)

**STATUS: GOOD — 8 issues, 3 significant**

| # | Severity | Finding | Fix |
|---|----------|---------|-----|
| F-1 | **HIGH** | `WsListener._send_heartbeat()` (line 1265-1273): Docstring says "Send ping frame to keep WS alive; called on timer every 20 seconds." This is wrong — same ping/pong issue as UML. WEEX server sends ping, client responds pong. This function should be `_handle_server_ping()` and send pong in reply, not initiate ping on a timer. | Rename to `_handle_server_ping(ws, server_time: str) -> None`. Called from `_on_message` when `event == "ping"`, responds with `{"event": "pong", "time": server_time}`. |
| F-2 | **HIGH** | `Executor.open_position()` (line 513-522): Entry signal type is `Signal` namedtuple with fields `symbol, direction, grade, sl_price, quantity`. But the Signal NamedTuple defined at line 1430-1438 has `symbol, direction, grade, sl_price, quantity, atr`. The `atr` field is present in the NamedTuple but NOT listed in the `open_position()` parameter description. The executor needs ATR for: (1) logging, (2) passing to risk_gate checks. Need to ensure open_position receives the full Signal or the ATR separately. | Verify that `signal.atr` is used by risk_gate.check_all() — it is (passed as `signal_atr` at line 814). Signal is passed as-is, so this works. The open_position docstring at line 517 should list `atr` in the Signal description. Minor doc fix. |
| F-3 | **MEDIUM** | `FourPillarsPlugin._compute_stochastic()` (line 1481-1490): Says Raw K with `smooth=1` which is correct per MEMORY.md constants. But the function computes K AND D — if Raw K means smooth=1, the D-line computation needs to use SMA(K, d_period) not EMA. The `d_period=3` is correct per Kurisko spec (9-3, 14-3, 40-3, 60-10). Needs to explicitly state "SMA smoothing, not EMA" in the docstring. | Add to docstring: "Raw K (smooth=1), D = SMA(K, d_period)." |
| F-4 | **MEDIUM** | Missing stochastic periods: The contracts define `STOCH_FAST_K=9` and `STOCH_CONFIRM_K=14` as module constants (lines 1421-1422), but do NOT define `STOCH_DIVERGENCE_K=40` and `STOCH_MACRO_K=60`. Per MEMORY.md reference constants: 9-3 (entry), 14-3 (confirm), 40-3 (divergence), 60-10 (macro). All four are needed for Four Pillars signal grading. | Add `STOCH_DIVERGENCE_K=40`, `STOCH_DIVERGENCE_D=3`, `STOCH_MACRO_K=60`, `STOCH_MACRO_D=10` to module constants. |
| F-5 | LOW | `StateManager.close_position()` (line 751-764): Parameter `realize_pnl` is named correctly but docstring says "Gross PnL from fill event (0 if unavailable)". Should clarify: this is the exchange-reported `realizePnl` from the WS fill, NOT the same as computed PnL. The function should also compute net PnL (gross - commission) for trades.csv. | Add note that net_pnl is computed internally from realize_pnl - commission. |
| F-6 | LOW | `ApiUtils.http_get()` (line 250-261): Docstring says "return parsed JSON or None on error". Prevention rule W16 says "helpers either always or never check error codes". GET endpoints have no wrapper, so there's no error code to check — this is consistent. POST endpoints return `{success, errorCode}` and the docstring for `http_post()` at line 263-272 says "returns raw dict always — caller checks success field" which is the W16 approach. Consistent. | None. |
| F-7 | **MEDIUM** | Missing `atr_at_entry` field in state position schema. The UML state schema (lines 420-429) does not include `atr_at_entry`. This field is needed for: (1) BE raise trigger calculation (entry + N * ATR), (2) TTP activation threshold, (3) trades.csv column. Without it, the BE raise and TTP cannot compute their thresholds. | Add `atr_at_entry: float` to the position state schema in both UML and function contracts. Update `StateManager.add_position()` to accept `atr_at_entry` parameter. |
| F-8 | **MEDIUM** | Missing `commission_rate_per_side` in state/config flow. The contracts mention `W07` (name commission vars explicitly) but there's no function for fetching/caching the commission rate at startup. `main.py:startup_checks()` mentions "fetch and log commission rates" but there's no corresponding function contract for storing the result. The executor needs the commission rate for PnL computation. | Add `fetch_commission_rate(symbol: str) -> float` to `api_utils.py` with `GET /capi/v3/account/commissionRate`. Cache the per-side rate. Make it available to executor and state_manager. |

**Function Contracts verdict**: Solid overall. Three significant gaps to address before Phase 6 build.

---

## Consolidated Critical Fixes (must fix before Phase 6 build)

| # | What | Where | Fix |
|---|------|-------|-----|
| 1 | **Ping/pong inverted** | UML Section 3 + FUNCTION-CONTRACTS `ws_listener.py` | Server sends ping, client responds pong. Remove client heartbeat timer. Add `_handle_server_ping()`. |
| 2 | **Missing `atr_at_entry`** | UML state schema + FUNCTION-CONTRACTS `state_manager.py` | Add to position dict. Required for BE raise and TTP activation thresholds. |
| 3 | **Missing stochastic constants** | FUNCTION-CONTRACTS `plugins/four_pillars.py` | Add all 4 stochastic periods (9-3, 14-3, 40-3, 60-10). |
| 4 | **Missing commission rate function** | FUNCTION-CONTRACTS `api_utils.py` | Add `fetch_commission_rate()` with caching. |

---

## Execution Plan

### Step 1: Run Phase 2 script (coin inventory)
- Give user the run command: `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\scripts\build_coin_index.py"`
- Await results. Review summary counts.
- Script is ready as-is — no fixes needed before running.

### Step 2: Fix UML document
Apply 1 critical fix to `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\docs\WEEX-CONNECTOR-UML.md`:
- Fix WSListener heartbeat section: server sends ping, client responds pong
- Add `atr_at_entry` to state schema

### Step 3: Fix Function Contracts document
Apply 4 fixes to `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\docs\FUNCTION-CONTRACTS.md`:
- Fix `_send_heartbeat` -> `_handle_server_ping`
- Add `atr_at_entry` to position state and `add_position()` params
- Add missing stochastic constants (40-3, 60-10)
- Add `fetch_commission_rate()` function contract

### Step 4: Update WEEX skill
Update `C:\Users\User\.claude\skills\weex\SKILL.md`:
- Fix ping/pong protocol description
- Update Phase Status (Phase 2 + Phase 3 now have artifacts)

### Step 5: Session log + INDEX update
- Write session log: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-03-13-weex-phase2-3-audit.md`
- Append to INDEX.md
- Update PROJECT-STATUS.md with WEEX phase progress

---

## Permissions Needed (batch approval)

1. **Edit tool** — Fix UML doc: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\docs\WEEX-CONNECTOR-UML.md`
2. **Edit tool** — Fix function contracts: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\docs\FUNCTION-CONTRACTS.md`
3. **Edit tool** — Update WEEX skill: `C:\Users\User\.claude\skills\weex\SKILL.md`
4. **Write tool** — Session log: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-03-13-weex-phase2-3-audit.md` (new file)
5. **Edit tool** — INDEX.md append
6. **Edit tool** — PROJECT-STATUS.md update
7. **Bash tool** — `ls` directory checks only (read-only)

No Python execution needed (user runs Phase 2 script themselves per hard rules).

---

## Verification

1. Phase 2 script: User runs, reports summary counts. We confirm CSV written.
2. UML fixes: Read back fixed sections, verify ping/pong and atr_at_entry.
3. Function contracts fixes: Read back, verify all 4 fixes applied.
4. Cross-check: Ensure UML and function contracts are consistent after fixes.
