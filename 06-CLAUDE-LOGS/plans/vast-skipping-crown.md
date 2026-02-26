# Vault Organization Build — Builds for the Night
**Date:** 2026-02-25
**Status:** Awaiting approval

## Context

The Obsidian vault has accumulated organizational debt across 5 areas: MEMORY.md exceeds its 200-line hard limit (215 lines, content truncated every session), 24+ session logs have no index, DASHBOARD-FILES.md is 9 days stale (says v3.8.4 production when v3.9.2 has been live), PRODUCT-BACKLOG.md is missing BingX connector/WEEX screener/Vince v2 items, and there is no single doc showing what systems are deployed. All of this is pure documentation work — zero code, zero risk, safe to run while AFK.

---

## Build Steps

### Step 1: MEMORY.md Refactoring (CRITICAL — content is being lost)

**Problem:** 215 lines, hard rule = 200 max. Lines 201-215 truncated every session.

**Action:** Split into index + 7 topic files in `C:\Users\User\.claude\projects\c--Users-User-Documents-Obsidian-Vault\memory\`

| New Topic File | Content Extracted | Lines Saved |
|---|---|---|
| `TOPIC-backtester.md` | Python Backtester section | ~15 |
| `TOPIC-commission-rules.md` | Commission + Engine Commission + Capital Model | ~67 |
| `TOPIC-bbw-pipeline.md` | BBW Simulator Pipeline + backlog BBW items | ~5 |
| `TOPIC-bingx-connector.md` | BingX Connector + Last/Previous Session | ~26 |
| `TOPIC-vince-v2.md` | Vince v2 + Screener sections + Session Logs | ~30 |
| `TOPIC-dashboard.md` | Dashboard section | ~13 |
| `TOPIC-critical-lessons.md` | Critical Lessons (currently truncated) | ~11 |

**Result:** MEMORY.md drops to ~80 lines (hard rules + build workflow + constants + environment + topic links). All detail preserved in topic files.

**Tools:** Write (new topic files), Edit (trim MEMORY.md, replace sections with links)
**Verify:** Line count under 200, grep key terms in topic files

---

### Step 2: Session Log Index

**Problem:** `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\` has 144 markdown files, no index.

**Action:** Create `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\INDEX.md`
- By-date table (newest first) with one-line summary per file
- By-topic grouping at bottom (BingX, BBW, Dashboard, Vince, Pine Script, Data, Infra, Strategy)
- Note duplicate build journals

**Tools:** Write (new file)
**Verify:** File count matches ls output

---

### Step 3: DASHBOARD-FILES.md Update

**File:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\DASHBOARD-FILES.md`

**Changes:**
- Production: v3.8.4 --> v3.9.2 (`scripts/dashboard_v392.py`, 2500L, STABLE)
- Next: v3.9.3 (BLOCKED — IndentationError at line 1972)
- Add v3.9.1, v3.9.2, v3.9.3 to active files table
- Move v3.8.4 to archived
- Add capital_model_v2.py (537L), pdf_exporter_v2.py (330L) to utils
- Update timestamp to 2026-02-25

**Tools:** Edit (existing file)

---

### Step 4: PRODUCT-BACKLOG.md Reconciliation

**File:** `C:\Users\User\Documents\Obsidian Vault\PRODUCT-BACKLOG.md`

**Add to P0 (Active):**
- BingX connector demo live (Step 1 ready, 67/67 tests, run main.py)
- Dashboard v3.9.3 bug fix (blocked on indentation)

**Add to P1 (High):**
- WEEX Screener build (scoped 2026-02-24, not built)
- Four Pillars Strategy Scoping (19 unknowns remaining)
- Vince v2 concept approval + plugin interface spec

**Add to Completed:**
- C.16 Dashboard v3.9.2
- C.17 BingX Connector 67/67 tests
- C.18 Screener v1 22/22 tests

**Mark DONE:** P0.1 (256-coin period gaps)
**Update:** Last updated --> 2026-02-25

**Tools:** Edit (existing file)

---

### Step 5: LIVE-SYSTEM-STATUS.md

**File:** `C:\Users\User\Documents\Obsidian Vault\LIVE-SYSTEM-STATUS.md` (new)

Single-page view:

| System | Version | Status | Run Command |
|---|---|---|---|
| Backtester Engine | v3.8.4 | PRODUCTION | (via dashboard) |
| Dashboard | v3.9.2 | PRODUCTION | `streamlit run "scripts/dashboard_v392.py"` |
| BingX Connector | v1.0 | DEMO READY | `python main.py` |
| WEEX Screener | -- | NOT BUILT | -- |
| Vince v2 | -- | CONCEPT ONLY | -- |

Plus infrastructure table (PostgreSQL, Ollama, Jacky VPS) and pending deployments list.

**Tools:** Write (new file)

---

## Post-Build: Save Plan Copy to Vault

Per CLAUDE.md, also save to: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-02-25-vault-organization-build.md`

---

## Execution Order

| # | Action | Tool | Risk |
|---|---|---|---|
| 1a | Create 7 TOPIC-*.md files | Write x7 | Zero (new files) |
| 1b | Trim MEMORY.md to index | Edit | Zero (replacing with links) |
| 1c | Verify line count < 200 | Read | -- |
| 2 | Create INDEX.md for session logs | Write | Zero (new file) |
| 3 | Update DASHBOARD-FILES.md | Edit | Zero (correcting stale info) |
| 4 | Update PRODUCT-BACKLOG.md | Edit | Zero (adding missing items) |
| 5 | Create LIVE-SYSTEM-STATUS.md | Write | Zero (new file) |

## Verification

- MEMORY.md: confirm under 200 lines, topic links resolve
- Topic files: grep key terms (e.g., "commission_rate=0.0008", "v3.9.2")
- INDEX.md: file count matches actual 06-CLAUDE-LOGS contents
- DASHBOARD-FILES.md: "v3.9.2" appears as production
- PRODUCT-BACKLOG.md: BingX + WEEX + Vince appear
- LIVE-SYSTEM-STATUS.md: all systems listed with correct versions
