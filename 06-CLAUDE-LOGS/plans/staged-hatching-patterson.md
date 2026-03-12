# Plan: Comprehensive Project Update Document (2026-03-11)

## Context

User wants a full project update covering:
1. All UML diagrams and their current status
2. Overall project progress across all components
3. Recent session activity (many logs since last update)
4. Output must be accessible to **Claude Desktop** and **Claude Web** (i.e., written to the Obsidian Vault where Claude Desktop's MCP can read it, and structured so it can be copy-pasted or linked)

The last PROJECT-STATUS.md update was 2026-03-10. The last PROJECT-OVERVIEW.md update was 2026-02-27 (very stale). PRODUCT-BACKLOG.md was last updated 2026-03-03. LIVE-SYSTEM-STATUS.md was last updated 2026-03-07.

---

## Deliverables

### 1. Update `PROJECT-STATUS.md` (Edit)
**File:** `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\PROJECT-STATUS.md`

Updates to apply:
- Add 55/89 strategy analysis results (8/9 coins negative, COUNTER_TREND 77.4% failure mode)
- Add S12 Macro Cycle strategy doc (cloud role correction)
- Add Strategy v4 research findings (S4 explains R:R=0.28, cascade overlap problem, 5 decisions pending)
- Add 55/89 engine + dashboard v3 (Backtester5589, 7/7 tests, dashboard v3 built)
- Update BingX v2 stats section
- Add GPU sweep 5589 (cuda_sweep_5589.py, py_compile PASS, not runtime-tested)

### 2. Update `PROJECT-OVERVIEW.md` (Major rewrite)
**File:** `C:\Users\User\Documents\Obsidian Vault\PROJECT-OVERVIEW.md`

This is the **cross-project master map** visible to Claude Desktop. Currently frozen at 2026-02-27. Needs:
- Update Mermaid diagram: BingX Bot v1.0 DEMO -> v2.0 LIVE, add 55/89 strategy branch, add Strategy v4 research node
- Update all status tables to current versions
- Update blockers (primary blocker shifted from "B1" to "Strategy v4 decisions" which gate B1)
- Update Next Actions to reflect current state
- Add UML inventory section (link to all 6 master diagrams + key session diagrams)

### 3. Update `PRODUCT-BACKLOG.md` (Edit)
**File:** `C:\Users\User\Documents\Obsidian Vault\PRODUCT-BACKLOG.md`

- Add completed items since 2026-03-03: BingX v2 live, 55/89 engine, 55/89 dashboard v3, negative coin analysis, S12 doc, strategy v4 research, v1/v2 mechanical fixes, git push for VPS
- Add new P0/P1 items: Strategy v4 decisions (5 open), 55/89 full portfolio sweep with P0-fixed params
- Update P0.6 (Vince B1) status note — now further blocked by strategy v4 decisions

### 4. Update `LIVE-SYSTEM-STATUS.md` (Edit)
**File:** `C:\Users\User\Documents\Obsidian Vault\LIVE-SYSTEM-STATUS.md`

- Add 55/89 Backtester engine + dashboard as new systems (BUILT status)
- Update BingX v2 detail section with latest stats
- Add 55/89 negative coin analysis results as data artifact

### 5. Create session log for this session
**File:** `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-03-11-project-update-session.md`

### 6. Update `INDEX.md` (Edit/append)
**File:** `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\INDEX.md`

- Append today's session log entry

---

## UML Diagram Inventory (to include in PROJECT-OVERVIEW.md)

Six master architecture diagrams exist:

| # | Diagram | File | Version | Status |
|---|---------|------|---------|--------|
| 1 | Project Overview (Master Map) | `PROJECT-OVERVIEW.md` | 2026-02-27 | STALE -- updating now |
| 2 | Four Pillars Strategy UML | `PROJECTS/four-pillars-backtester/docs/FOUR-PILLARS-STRATEGY-UML.md` | v2.0 (2026-02-20) | CURRENT but describes v3.8.4 state machine (pre-v4 research) |
| 3 | BingX Connector UML | `PROJECTS/bingx-connector-v2/docs/BINGX-CONNECTOR-UML.md` | v3.0 (2026-03-03) | CURRENT |
| 4 | Vince ML UML | `PROJECTS/four-pillars-backtester/docs/vince-ml/VINCE-ML-UML-DIAGRAMS.md` | 2026-02-18 | CURRENT (concept level, no code changes since) |
| 5 | BBW v2 UML | `PROJECTS/four-pillars-backtester/docs/bbw-v2/BBW-V2-UML-DIAGRAMS.md` | v2.1 (2026-02-17) | CURRENT (pipeline complete) |
| 6 | 55/89 Scalp Strategy UML | `02-STRATEGY/Research/strategy-55-89-cross-uml.mermaid` | 2026-03-06 | NEW -- needs validation against backtester results |

Additional diagrams:
- `VINCE-FLOW.md` — Vince training loop + Gantt schedule
- `PROJECT-FLOW-CHRONOLOGICAL.md` — 5-phase build flow (updated 2026-02-14, stale)
- `BBW-V2-ARCHITECTURE.md` — Simplified PDF-friendly version
- `uml/` sandbox directory — 3 exploration files
- 30+ session logs contain inline Mermaid diagrams

### UML Staleness Assessment

| Diagram | Stale? | Why |
|---------|--------|-----|
| Strategy UML (v2.0) | YES | Describes v3.8.4 state machine. Strategy v4 research (2026-03-10) found S4 code inverts the intended model. UML needs v4 update once 5 decisions are made. |
| Project Overview | YES | Frozen at 2026-02-27. Bot is now v2.0 LIVE, not v1.0 DEMO. Many new components. |
| BingX Connector UML | NO | v3.0 is current. v2 bot matches this architecture. |
| Vince ML UML | NO | Concept-level, no code written since. Accurate for what exists. |
| BBW v2 UML | NO | Pipeline complete, no changes since. |
| 55/89 UML | PARTIAL | Mermaid file exists but backtester results (8/9 negative) suggest the strategy spec may need revision. |
| Project Flow Chronological | YES | Last updated 2026-02-14. Many phases have progressed. |

---

## Execution Order

1. Edit `PROJECT-STATUS.md` — add new findings, update tables
2. Rewrite `PROJECT-OVERVIEW.md` — new Mermaid diagram, updated tables, UML inventory, current blockers
3. Edit `PRODUCT-BACKLOG.md` — add completions, new tasks, update statuses
4. Edit `LIVE-SYSTEM-STATUS.md` — add 55/89 systems, update BingX detail
5. Create session log `2026-03-11-project-update-session.md`
6. Edit `INDEX.md` — append session entry
7. Validate: read back all 4 updated files to confirm accuracy

---

## Claude Desktop / Claude Web Access

- **Claude Desktop**: reads the Obsidian Vault via MCP filesystem. All files above are in the vault. `PROJECT-OVERVIEW.md` at vault root is the best single entry point.
- **Claude Web**: cannot read local files. User can copy-paste `PROJECT-OVERVIEW.md` or `PROJECT-STATUS.md` into a Claude Web conversation as context. The documents are structured to be self-contained for this purpose.
- **Alternative**: If user wants a dedicated briefing doc for pasting into Claude Web, I can create a single `PROJECT-BRIEFING-2026-03-11.md` that combines the key info from all 4 files into one portable document. This would go in `06-CLAUDE-LOGS/` and be optimized for copy-paste into any LLM.

---

## Verification

1. Read back each edited file to confirm no data corruption
2. Confirm Mermaid diagram renders (syntax check)
3. Confirm all dates and version numbers match source logs
4. Confirm no MEMORY.md hard rules violated (full paths, no emojis, timestamps)
